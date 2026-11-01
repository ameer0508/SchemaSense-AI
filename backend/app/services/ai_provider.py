"""AI Provider service architecture for SchemaSense AI.

Provides:
- BaseAIProvider abstract interface
- LocalTransformersProvider: real local Hugging Face transformer inference (Qwen/Qwen2.5-Coder-1.5B-Instruct)
- MockAIProvider: high-fidelity deterministic provider for unit testing without downloading model weights
- Lazy initialization and thread-safe inference execution
- Status monitoring and capability discovery
"""

import asyncio
import re
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.exceptions import (
    ModelInferenceException,
    ModelUnavailableException,
)
from app.core.logging import get_logger
from app.schemas.ai import ModelLoadStatus, ModelStatusResponse
from app.services.interfaces import BaseAIProvider, SchemaMetadata, SQLGenerationResult, SQLCorrectionResult
from app.services.prompt_builder import (
    PromptBuilder,
    CorrectionPromptBuilder,
    extract_structured_response,
    extract_structured_correction_response,
)

logger = get_logger("ai_provider")


class AbstractAIProvider(BaseAIProvider, ABC):
    """Extended interface for AI providers including status and lifecycle."""

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Model identifier."""
        pass

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize and preload model resources."""
        pass

    @abstractmethod
    def get_status(self) -> ModelStatusResponse:
        """Return accurate operational status."""
        pass


class MockAIProvider(AbstractAIProvider):
    """High-fidelity deterministic mock provider for unit testing and offline development."""

    def __init__(self, model_id: str = "mock-qwen-coder-1.5b") -> None:
        self._provider_name = "mock"
        self._model_id = model_id
        self._prompt_builder = PromptBuilder()

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def model_id(self) -> str:
        return self._model_id

    async def initialize(self) -> bool:
        return True

    def get_status(self) -> ModelStatusResponse:
        return ModelStatusResponse(
            provider="mock",
            model_id=self._model_id,
            status="ready",
            device="cpu",
            is_available=True,
            is_loading=False,
            total_params="1.54B (mocked)",
            max_new_tokens=settings.AI_MAX_NEW_TOKENS,
            temperature=settings.AI_TEMPERATURE,
        )

    async def generate_sql(
        self,
        question: str,
        schema: SchemaMetadata,
        dialect: str = "sqlite",
        context: Optional[Dict[str, Any]] = None,
    ) -> SQLGenerationResult:
        """Generate realistic deterministic SQL grounded in schema for tests."""
        q_lower = question.lower()
        table_names = [t.get("name") for t in schema.tables] if schema.tables else []

        # 1. Top students / GPA
        if "top" in q_lower and ("student" in q_lower or "gpa" in q_lower or "cgpa" in q_lower):
            limit = 5
            limit_match = re.search(r"\b(\d+)\b", q_lower)
            if limit_match:
                limit = int(limit_match.group(1))
            return SQLGenerationResult(
                sql=f"SELECT student_id, first_name, last_name, gpa FROM students ORDER BY gpa DESC LIMIT {limit};",
                explanation=f"Selects top {limit} students ranked by GPA in descending order.",
                confidence_score=0.98,
                tokens_used=42,
                assumptions=[f"Assumed highest GPA first with LIMIT {limit}."],
            )

        # 2. Count queries
        if "how many" in q_lower or "count" in q_lower:
            target_table = "students"
            for tbl in table_names:
                if tbl.lower() in q_lower or tbl.lower()[:-1] in q_lower:
                    target_table = tbl
                    break
            return SQLGenerationResult(
                sql=f"SELECT COUNT(*) AS total_{target_table} FROM {target_table};",
                explanation=f"Calculates the total count of records in table '{target_table}'.",
                confidence_score=0.95,
                tokens_used=30,
                assumptions=["Count all matching rows."],
            )

        # 3. Multi-table JOIN (students & departments)
        if "department" in q_lower and "student" in q_lower:
            return SQLGenerationResult(
                sql=(
                    "SELECT s.first_name, s.last_name, d.department_name "
                    "FROM students s "
                    "JOIN departments d ON s.department_id = d.department_id "
                    "LIMIT 50;"
                ),
                explanation="Joins students with their corresponding department using department_id.",
                confidence_score=0.94,
                tokens_used=65,
                assumptions=["Applied LIMIT 50 to prevent unbounded output."],
            )

        # 4. Courses & Faculty
        if "course" in q_lower and "faculty" in q_lower:
            return SQLGenerationResult(
                sql=(
                    "SELECT c.title, c.code, f.first_name, f.last_name "
                    "FROM courses c "
                    "JOIN faculty f ON c.faculty_id = f.faculty_id "
                    "LIMIT 50;"
                ),
                explanation="Retrieves courses alongside their instructor details.",
                confidence_score=0.93,
                tokens_used=58,
                assumptions=["Joined on faculty_id foreign key."],
            )

        # 5. Default fallback to first table
        primary_table = table_names[0] if table_names else "students"
        return SQLGenerationResult(
            sql=f"SELECT * FROM {primary_table} LIMIT 20;",
            explanation=f"Retrieves preview records from table '{primary_table}'.",
            confidence_score=0.85,
            tokens_used=25,
            assumptions=["Defaulted to LIMIT 20 on primary table."],
        )

    async def generate_correction(
        self,
        question: str,
        failed_sql: str,
        error_category: str,
        error_message: str,
        schema: SchemaMetadata,
        dialect: str = "sqlite",
        context: Optional[Dict[str, Any]] = None,
    ) -> SQLCorrectionResult:
        """Deterministic repair logic for testing self-correction pipelines."""
        changes = []
        sql = failed_sql

        # 1. Unknown column repair: e.g. student_name -> first_name, last_name
        if "student_name" in failed_sql.lower() or "column" in error_category.lower():
            sql = re.sub(r"\bstudent_name\b", "first_name, last_name", sql, flags=re.IGNORECASE)
            changes.append("Replaced hallucinated 'student_name' column with 'first_name, last_name' from schema.")

        # 2. Unknown table repair: e.g. student_records -> students
        if "student_records" in failed_sql.lower() or "table" in error_category.lower():
            sql = re.sub(r"\bstudent_records\b", "students", sql, flags=re.IGNORECASE)
            changes.append("Corrected table reference from 'student_records' to verified table 'students'.")

        # 3. Dialect/Syntax or Multiplicative Join repair:
        if "enrollments" in failed_sql.lower() and ("multiplicative" in error_category.lower() or "join" in error_category.lower()):
            sql = "SELECT student_id, first_name, last_name, gpa FROM students ORDER BY gpa DESC LIMIT 5;"
            changes.append("Removed unnecessary 1-to-N JOIN on enrollments table to prevent row multiplication.")

        # 4. If query is still identical or not repaired, fall back to clean query based on question
        if sql == failed_sql:
            clean_res = await self.generate_sql(question, schema, dialect, context)
            sql = clean_res.sql
            changes.append("Regenerated query using verified schema catalog.")

        return SQLCorrectionResult(
            sql=sql,
            explanation=f"Repaired SQL based on diagnostic '{error_category}'.",
            changes_made=changes,
            tokens_used=45,
        )


class LocalTransformersProvider(AbstractAIProvider):
    """Local generative AI provider using Hugging Face Transformers and Qwen2.5-Coder."""

    def __init__(
        self,
        model_id: str = "Qwen/Qwen2.5-Coder-1.5B-Instruct",
        device: Optional[str] = None,
    ) -> None:
        self._provider_name = "local"
        self._model_id = model_id or settings.LOCAL_MODEL_ID
        self._prompt_builder = PromptBuilder()

        # Determine runtime execution device
        if device and device != "auto":
            self._device = device
        else:
            try:
                import torch
                self._device = "cuda" if torch.cuda.is_available() else "cpu"
            except Exception:
                self._device = "cpu"

        self._status: ModelLoadStatus = "not_loaded"
        self._error_message: Optional[str] = None
        self._model: Optional[Any] = None
        self._tokenizer: Optional[Any] = None

        # Locks for thread safety
        self._init_lock = asyncio.Lock()
        self._inference_lock = asyncio.Lock()

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def device(self) -> str:
        return self._device

    def get_status(self) -> ModelStatusResponse:
        """Report current model status without blocking or triggering loads."""
        return ModelStatusResponse(
            provider="local",
            model_id=self._model_id,
            status=self._status,
            device=self._device,
            is_available=(self._status == "ready"),
            is_loading=(self._status == "loading"),
            total_params="1.54B",
            max_new_tokens=settings.AI_MAX_NEW_TOKENS,
            temperature=settings.AI_TEMPERATURE,
            error_message=self._error_message,
        )

    def _load_model_sync(self) -> None:
        """Synchronously load tokenizer and model weights into memory (runs in worker thread)."""
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        logger.info("Loading tokenizer for model '%s'...", self._model_id)
        self._tokenizer = AutoTokenizer.from_pretrained(
            self._model_id,
            cache_dir=settings.AI_MODEL_CACHE_DIR,
            trust_remote_code=True,
        )

        logger.info(
            "Loading model weights for '%s' onto device '%s'...",
            self._model_id,
            self._device,
        )

        dtype = torch.float32
        if self._device == "cuda":
            dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16

        self._model = AutoModelForCausalLM.from_pretrained(
            self._model_id,
            torch_dtype=dtype,
            cache_dir=settings.AI_MODEL_CACHE_DIR,
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )
        self._model.to(self._device)
        self._model.eval()
        logger.info("Model '%s' successfully loaded and ready for inference.", self._model_id)

    async def initialize(self) -> bool:
        """Thread-safe lazy initialization of model resources."""
        if self._status == "ready" and self._model is not None:
            return True

        async with self._init_lock:
            # Double-check inside lock
            if self._status == "ready" and self._model is not None:
                return True

            self._status = "loading"
            self._error_message = None

            try:
                # Run synchronous model download and load in separate worker thread
                await asyncio.to_thread(self._load_model_sync)
                self._status = "ready"
                self._error_message = None
                return True
            except Exception as e:
                logger.error("Failed to load model '%s': %s", self._model_id, str(e), exc_info=True)
                self._status = "error"
                self._error_message = str(e)
                raise ModelUnavailableException(
                    message=f"Failed to load AI model '{self._model_id}': {str(e)}",
                    details={"model_id": self._model_id, "device": self._device},
                )

    def _run_inference_sync(
        self,
        prompt_text: str,
        temperature: float,
        max_new_tokens: int,
    ) -> str:
        """Synchronously execute autoregressive token generation (runs in worker thread)."""
        import torch

        if self._model is None or self._tokenizer is None:
            raise RuntimeError("Model or tokenizer is not initialized.")

        inputs = self._tokenizer(prompt_text, return_tensors="pt")
        inputs = {k: v.to(self._device) for k, v in inputs.items()}
        input_token_len = inputs["input_ids"].shape[1]

        gen_kwargs: Dict[str, Any] = {
            "max_new_tokens": max_new_tokens,
            "pad_token_id": self._tokenizer.eos_token_id,
        }

        if temperature > 0.0:
            gen_kwargs["do_sample"] = True
            gen_kwargs["temperature"] = temperature
            gen_kwargs["top_p"] = 0.95
        else:
            gen_kwargs["do_sample"] = False

        with torch.inference_mode():
            output_tokens = self._model.generate(**inputs, **gen_kwargs)

        # Slice off prompt tokens to decode only generated tokens
        new_tokens = output_tokens[0][input_token_len:]
        decoded_output = self._tokenizer.decode(new_tokens, skip_special_tokens=True)
        return decoded_output

    async def generate_sql(
        self,
        question: str,
        schema: SchemaMetadata,
        dialect: str = "sqlite",
        context: Optional[Dict[str, Any]] = None,
    ) -> SQLGenerationResult:
        """Generate SQL query using local transformer model inference."""
        if self._status != "ready" or self._model is None:
            logger.info("Model not yet initialized. Triggering lazy initialization...")
            await self.initialize()

        # Build schema text from context or schema object
        schema_text = ""
        if context and "schema_context" in context:
            schema_text = context["schema_context"]
        else:
            table_defs = []
            for t in schema.tables:
                col_defs = [f"{c.get('name')}: {c.get('data_type')}" for c in t.get("columns", [])]
                table_defs.append(f"- {t.get('name')}: ({', '.join(col_defs)})")
            schema_text = "\n".join(table_defs)

        # Build prompt using chat messages
        chat_messages = self._prompt_builder.build_chat_messages(
            question=question,
            schema_context=schema_text,
            dialect=dialect,
        )

        # Apply chat template
        if hasattr(self._tokenizer, "apply_chat_template"):
            prompt_str = self._tokenizer.apply_chat_template(
                chat_messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        else:
            prompt_str = self._prompt_builder.build_flat_prompt(
                question=question,
                schema_context=schema_text,
                dialect=dialect,
            )

        temperature = context.get("temperature", settings.AI_TEMPERATURE) if context else settings.AI_TEMPERATURE
        max_tokens = settings.AI_MAX_NEW_TOKENS

        # Execute inference protected by concurrency lock
        async with self._inference_lock:
            try:
                start_time = time.perf_counter()
                raw_generated_text = await asyncio.to_thread(
                    self._run_inference_sync,
                    prompt_str,
                    temperature,
                    max_tokens,
                )
                duration = time.perf_counter() - start_time
                logger.debug("Local inference completed in %.2f seconds.", duration)
            except Exception as e:
                logger.error("Inference execution failed: %s", str(e), exc_info=True)
                raise ModelInferenceException(
                    message=f"Generation failed during transformer inference: {str(e)}",
                    details={"model_id": self._model_id},
                )

        # Parse structured response
        sql, explanation, assumptions = extract_structured_response(raw_generated_text)

        return SQLGenerationResult(
            sql=sql,
            explanation=explanation,
            confidence_score=0.90,
            tokens_used=len(raw_generated_text.split()),
            assumptions=assumptions,
        )

    async def generate_correction(
        self,
        question: str,
        failed_sql: str,
        error_category: str,
        error_message: str,
        schema: SchemaMetadata,
        dialect: str = "sqlite",
        context: Optional[Dict[str, Any]] = None,
    ) -> SQLCorrectionResult:
        """Generate corrected SQL using local transformer model inference."""
        if self._status != "ready" or self._model is None:
            logger.info("Model not yet initialized for correction. Triggering initialization...")
            await self.initialize()

        # Build schema text from context or schema object
        schema_text = ""
        if context and "schema_context" in context:
            schema_text = context["schema_context"]
        else:
            table_defs = []
            for t in schema.tables:
                col_defs = [f"{c.get('name')}: {c.get('data_type')}" for c in t.get("columns", [])]
                table_defs.append(f"- {t.get('name')}: ({', '.join(col_defs)})")
            schema_text = "\n".join(table_defs)

        correction_builder = CorrectionPromptBuilder()
        chat_messages = correction_builder.build_correction_messages(
            question=question,
            schema_context=schema_text,
            failed_sql=failed_sql,
            error_category=error_category,
            error_message=error_message,
            dialect=dialect,
        )

        if hasattr(self._tokenizer, "apply_chat_template"):
            prompt_str = self._tokenizer.apply_chat_template(
                chat_messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        else:
            prompt_str = f"{chat_messages[0]['content']}\n\nUser:\n{chat_messages[1]['content']}\n\nAssistant:\n```json\n"

        temperature = context.get("temperature", 0.0) if context else 0.0
        max_tokens = settings.AI_MAX_NEW_TOKENS

        async with self._inference_lock:
            try:
                start_time = time.perf_counter()
                raw_generated_text = await asyncio.to_thread(
                    self._run_inference_sync,
                    prompt_str,
                    temperature,
                    max_tokens,
                )
                duration = time.perf_counter() - start_time
                logger.debug("Local correction inference completed in %.2f seconds.", duration)
            except Exception as e:
                logger.error("Correction inference failed: %s", str(e), exc_info=True)
                raise ModelInferenceException(
                    message=f"Correction failed during transformer inference: {str(e)}",
                    details={"model_id": self._model_id},
                )

        sql, explanation, changes_made = extract_structured_correction_response(raw_generated_text)

        return SQLCorrectionResult(
            sql=sql,
            explanation=explanation,
            changes_made=changes_made,
            tokens_used=len(raw_generated_text.split()),
        )


# Backward compatibility alias
AIProviderService = LocalTransformersProvider


# Global provider instance
_active_provider: Optional[AbstractAIProvider] = None


def get_ai_provider() -> AbstractAIProvider:
    """Return the active AI provider singleton according to system configuration."""
    global _active_provider
    if _active_provider is None:
        provider_name = settings.AI_PROVIDER.lower().strip()
        if provider_name == "mock":
            _active_provider = MockAIProvider(model_id="mock-qwen-coder-1.5b")
        else:
            _active_provider = LocalTransformersProvider(
                model_id=settings.LOCAL_MODEL_ID,
                device=settings.AI_DEVICE,
            )
    return _active_provider


def set_ai_provider(provider: AbstractAIProvider) -> None:
    """Explicitly inject a provider instance (useful for testing)."""
    global _active_provider
    _active_provider = provider
