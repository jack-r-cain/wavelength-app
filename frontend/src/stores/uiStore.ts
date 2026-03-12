import { create } from 'zustand'

export type ActiveTab = 'collection' | 'chat' | 'insights'

interface UIState {
  activeTab: ActiveTab
  isModalOpen: boolean
  selectedItemIds: number[]

  setActiveTab: (tab: ActiveTab) => void
  openModal: () => void
  closeModal: () => void
  toggleSelection: (id: number) => void
  clearSelection: () => void
}

export const useUIStore = create<UIState>((set) => ({
  activeTab: 'collection',
  isModalOpen: false,
  selectedItemIds: [],

  setActiveTab: (tab) => set({ activeTab: tab }),
  openModal: () => set({ isModalOpen: true }),
  closeModal: () => set({ isModalOpen: false }),

  toggleSelection: (id) =>
    set((state) => ({
      selectedItemIds: state.selectedItemIds.includes(id)
        ? state.selectedItemIds.filter((itemId) => itemId !== id)
        : [...state.selectedItemIds, id],
    })),

  clearSelection: () => set({ selectedItemIds: [] }),
}))
