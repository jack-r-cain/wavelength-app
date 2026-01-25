import { AddItemForm } from './components/AddItemForm'
import { ItemList } from './components/ItemList'

function App() {
  return (
    <div className='min-h-screen bg-gray-50 p-8'>
      <div className='max-w-6xl mx-auto'>
        <h1 className='text-4xl font-bold mb-8'>Wavelength</h1>

        <div className='grid grid-cols-1 lg:grid-cols-3 gap-8'>
          {/* Form takes 1 column */}
          <div className='lg:col-span-1'>
            <h2 className='text-2xl font-bold mb-4'>Add Item</h2>
            <AddItemForm />
          </div>

          {/* List takes 2 columns */}
          <div className='lg:col-span-2'>
            <h2 className='text-2xl font-bold mb-4'>Your Collection</h2>
            <ItemList />
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
