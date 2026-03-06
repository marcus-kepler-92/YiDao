import { create } from "zustand"

interface ChatState {
  activeBucketId: string | null
  sidebarOpen: boolean
  inputDraft: string
  setActiveBucket: (id: string | null) => void
  toggleSidebar: () => void
  setInputDraft: (draft: string) => void
}

export const useChatStore = create<ChatState>((set) => ({
  activeBucketId: null,
  sidebarOpen: true,
  inputDraft: "",
  setActiveBucket: (id) => set({ activeBucketId: id }),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setInputDraft: (draft) => set({ inputDraft: draft }),
}))
