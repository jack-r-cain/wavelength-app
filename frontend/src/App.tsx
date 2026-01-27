import { AddItemForm } from './components/AddItemForm'
import { ItemList } from './components/ItemList'
import { Searchbar } from './components/Searchbar'
import { AskQuestion } from './components/AskQuestion'
import { FindConnections } from './components/FindConnections'

function App() {
  return (
    <div className='min-h-screen bg-gray-50 p-8'>
      <div className='max-w-7xl mx-auto space-y-8'>
        <h1 className='text-4xl font-bold'>Wavelength</h1>

        {/* Search */}
        <section>
          <h2 className='text-2xl font-bold mb-4'>Search</h2>
          <Searchbar />
        </section>

        {/* AI Features - side by side */}
        <section className='grid grid-cols-1 lg:grid-cols-2 gap-8'>
          <div>
            <h2 className='text-2xl font-bold mb-4'>Ask About Your Taste</h2>
            <AskQuestion />
          </div>

          <div>
            <h2 className='text-2xl font-bold mb-4'>Find Connections</h2>
            <FindConnections />
          </div>
        </section>

        {/* Add & View */}
        <section className='grid grid-cols-1 lg:grid-cols-3 gap-8'>
          <div className='lg:col-span-1'>
            <h2 className='text-2xl font-bold mb-4'>Add Item</h2>
            <AddItemForm />
          </div>

          <div className='lg:col-span-2'>
            <h2 className='text-2xl font-bold mb-4'>Your Collection</h2>
            <ItemList />
          </div>
        </section>
      </div>
    </div>
  )
}

export default App
