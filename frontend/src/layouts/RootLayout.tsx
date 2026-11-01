import { useCallback, useEffect, useState } from 'react'
import { Outlet, useNavigate } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { TopNav } from './TopNav'
import { MobileNav } from './MobileNav'
import { CapabilityModal } from '@/components/workspace/CapabilityModal'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'

export function RootLayout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [capabilitiesModalOpen, setCapabilitiesModalOpen] = useState(false)
  const navigate = useNavigate()

  const handleFocusComposer = useCallback(() => {
    navigate('/')
    setTimeout(() => {
      const composer = document.getElementById('natural-language-composer')
      if (composer) {
        composer.focus()
      }
    }, 50)
  }, [navigate])

  // Global keyboard shortcut: Ctrl+K / Cmd+K to focus composer
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        handleFocusComposer()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleFocusComposer])

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-canvas text-foreground antialiased font-sans">
      {/* Accessible Skip Link */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-3 focus:left-3 focus:z-50 focus:rounded-[8px] focus:bg-indigo-600 focus:px-4 focus:py-2 focus:text-xs focus:font-semibold focus:text-white focus:shadow-lg focus:outline-none"
      >
        Skip to main content
      </a>

      {/* Desktop Sidebar */}
      <Sidebar onOpenCapabilities={() => setCapabilitiesModalOpen(true)} />

      {/* Mobile Drawer */}
      <MobileNav
        isOpen={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
        onOpenCapabilities={() => setCapabilitiesModalOpen(true)}
      />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Navigation */}
        <TopNav
          onOpenMobileMenu={() => setMobileMenuOpen(true)}
          onOpenCapabilities={() => setCapabilitiesModalOpen(true)}
          onFocusComposer={handleFocusComposer}
        />

        {/* Scrollable Page Body */}
        <main
          id="main-content"
          tabIndex={-1}
          className="flex-1 overflow-y-auto px-4 py-6 sm:px-8 sm:py-8 focus:outline-none"
        >
          <div className="mx-auto max-w-7xl">
            <ErrorBoundary fallbackTitle="Workspace View Error">
              <Outlet />
            </ErrorBoundary>
          </div>
        </main>
      </div>

      {/* Global Capabilities Discovery Modal */}
      <CapabilityModal
        isOpen={capabilitiesModalOpen}
        onClose={() => setCapabilitiesModalOpen(false)}
      />
    </div>
  )
}
