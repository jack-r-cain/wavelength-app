import type { ReactNode } from 'react'

import { Tabs } from './components/Tabs'
import { Modal } from './components/Modal'
import { AddItemForm } from './components/AddItemForm'
import { ItemList } from './components/ItemList'
import { Searchbar } from './components/Searchbar'
import { ChatInterface } from './components/ChatInterface'
import { FindConnections } from './components/FindConnections'
import { useUIStore } from './stores/uiStore'
import type { ActiveTab } from './stores/uiStore'

function App() {
  const activeTab = useUIStore((state) => state.activeTab)
  const setActiveTab = useUIStore((state) => state.setActiveTab)
  const isModalOpen = useUIStore((state) => state.isModalOpen)
  const openModal = useUIStore((state) => state.openModal)
  const closeModal = useUIStore((state) => state.closeModal)

  const tabs: { id: ActiveTab; label: string; content: ReactNode }[] = [
    {
      id: 'collection',
      label: '📚 Collection',
      content: (
        <div className='space-y-4'>
          <div className='flex justify-between items-center'>
            <h2 className='text-2xl font-bold'>Your Collection</h2>
            <button
              onClick={openModal}
              className='px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2'>
              <span>➕</span>
              <span>Add Item</span>
            </button>
          </div>

          <div>
            <h3 className='text-lg font-semibold mb-3'>Search</h3>
            <Searchbar />
          </div>

          <div>
            <h3 className='text-lg font-semibold mb-3'>All Items</h3>
            <ItemList />
          </div>
        </div>
      ),
    },
    {
      id: 'chat',
      label: '💬 Chat',
      content: (
        <div className='max-w-4xl mx-auto'>
          <h2 className='text-2xl font-bold mb-4'>Chat About Your Taste</h2>
          <ChatInterface />
        </div>
      ),
    },
    {
      id: 'insights',
      label: '🔍 Insights',
      content: (
        <div className='max-w-4xl mx-auto'>
          <h2 className='text-2xl font-bold mb-4'>Find Connections</h2>
          <FindConnections />
        </div>
      ),
    },
  ]

  return (
    <div className='min-h-screen bg-gray-50'>
      <header className='bg-white border-b sticky top-0 z-10'>
        <div className='max-w-7xl mx-auto px-8 py-1'>
          <h1 className='text-3xl font-bold'>Wavelength</h1>
          <p className='text-gray-600 text-sm mt-1'>Find what resonates</p>
        </div>
      </header>

      <main className='max-w-7xl mx-auto px-8'>
        <Tabs
          tabs={tabs}
          activeTab={activeTab}
          onTabChange={(tabId) => setActiveTab(tabId as ActiveTab)}
        />
      </main>

      <Modal isOpen={isModalOpen} onClose={closeModal} title='Add New Item'>
        <AddItemForm onSuccess={closeModal} />
      </Modal>
    </div>
  )
}

export default App
