import type { ReactNode } from 'react'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  children: ReactNode
}

export function Modal({ isOpen, onClose, title, children }: ModalProps) {
  if (!isOpen) return null

  return (
    <div className='fixed inset-0 z-50 overflow-y-auto'>
      {/* Backdrop */}
      <div
        className='fixed inset-0 bg-black bg-opacity-50 transition-opacity'
        onClick={onClose}
      />

      {/* Modal */}
      <div className='flex min-h-full items-center justify-center p-4'>
        <div className='relative bg-white rounded-lg shadow-xl max-w-md w-full p-6'>
          {/* Header */}
          <div className='flex items-center justify-between mb-4'>
            <h3 className='text-xl font-bold'>{title}</h3>
            <button
              onClick={onClose}
              className='text-gray-400 hover:text-gray-600 text-2xl leading-none'>
              ×
            </button>
          </div>

          {/* Content */}
          <div>{children}</div>
        </div>
      </div>
    </div>
  )
}
