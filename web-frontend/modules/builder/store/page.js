import { StoreItemLookupError } from '@baserow/modules/core/errors'
import { BuilderApplicationType } from '@baserow/modules/builder/applicationTypes'
import PageService from '@baserow/modules/builder/services/page'

export function populatePage(page) {
  page._ = {
    selected: false,
  }
  return page
}

const state = {
  selected: {},
}

const mutations = {
  ADD_ITEM(state, { builder, page }) {
    populatePage(page)
    builder.pages.push(page)
  },
  SET_SELECTED(state, { builder, page }) {
    Object.values(builder.pages).forEach((item) => {
      item._.selected = false
    })
    page._.selected = true
    state.selected = page
  },
}

const actions = {
  async selectById({ commit, dispatch }, { builderId, pageId }) {
    const builder = await dispatch('application/selectById', builderId, {
      root: true,
    })
    const type = BuilderApplicationType.getType()

    // Check if the just selected application is a builder
    if (builder.type !== type) {
      throw new StoreItemLookupError(
        `The application doesn't have the required ${type} type.`
      )
    }

    // Check if the provided page id is found in the just selected builder.
    const index = builder.pages.findIndex((item) => item.id === pageId)
    if (index === -1) {
      throw new StoreItemLookupError(
        'The page is not found in the selected application.'
      )
    }
    const page = builder.pages[index]

    commit('SET_SELECTED', { builder, page })

    return { builder, page }
  },
  async add({ commit, dispatch }, { builder, name }) {
    const { data: page } = await PageService(this.$client).create(
      builder.id,
      name
    )

    commit('ADD_ITEM', { builder, page })

    dispatch('selectById', { builderId: builder.id, pageId: page.id })
  },
}

const getters = {}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}