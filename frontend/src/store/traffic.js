import { defineStore } from 'pinia'

export const useTrafficStore = defineStore('traffic', {
  state: () => ({
    sections: [],
    selectedSectionId: null,
    realtimeData: {},
    isLoading: false,
  }),
  actions: {
    selectSection(id) { this.selectedSectionId = id },
    updateRealtime(data) { this.realtimeData[data.section_id] = data },
  },
})
