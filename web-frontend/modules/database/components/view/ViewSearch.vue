<template>
  <div>
    <a
      ref="contextLink"
      class="header__filter-link"
      :class="{
        'active--primary': headerSearchTerm.length > 0,
      }"
      @click="$refs.context.toggle($refs.contextLink, 'bottom', 'right', 4)"
    >
      <i class="header__search-icon iconoir-search"></i>
      {{ headerSearchTerm }}
    </a>
    <ViewSearchContext
      ref="context"
      :view="view"
      :fields="fields"
      :store-prefix="storePrefix"
      :always-hide-rows-not-matching-search="alwaysHideRowsNotMatchingSearch"
      @refresh="$emit('refresh', $event)"
      @search-changed="searchChanged"
    ></ViewSearchContext>
  </div>
</template>

<script>
import ViewSearchContext from '@baserow/modules/database/components/view/ViewSearchContext'

export default {
  name: 'ViewSearch',
  components: { ViewSearchContext },
  props: {
    view: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    storePrefix: {
      type: String,
      required: true,
    },
    alwaysHideRowsNotMatchingSearch: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data: () => {
    return {
      headerSearchTerm: '',
    }
  },
  mounted() {
    this.$priorityBus.$on(
      'start-search',
      this.$priorityBus.level.LOW,
      this.searchStarted
    )
  },
  beforeDestroy() {
    this.$priorityBus.$off('start-search', this.searchStarted)
  },
  methods: {
    searchChanged(newSearch) {
      this.headerSearchTerm = newSearch
    },
    searchStarted({ event }) {
      event.preventDefault()
      this.$bus.$emit('close-modals')
      this.$refs.contextLink.click()
    },
  },
}
</script>
