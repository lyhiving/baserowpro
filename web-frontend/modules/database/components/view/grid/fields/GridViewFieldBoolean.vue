<template>
  <div class="grid-view__cell active">
    <div class="grid-field-boolean">
      <div
        class="grid-field-boolean__checkbox"
        :class="{
          active: value,
          'grid-field-boolean__checkbox--read-only': readOnly,
        }"
        @click="toggle(value)"
      >
        <i class="iconoir-check grid-field-boolean__checkbox-icon"></i>
      </div>
    </div>
  </div>
</template>

<script>
import gridField from '@baserow/modules/database/mixins/gridField'

export default {
  mixins: [gridField],
  methods: {
    select() {
      // While the field is selected we want to toggle the value by pressing the enter
      // key.
      this.$el.keydownEvent = (event) => {
        if (event.key === 'Enter') {
          this.toggle(this.value)
        }
      }
      document.body.addEventListener('keydown', this.$el.keydownEvent)
    },
    beforeUnSelect() {
      document.body.removeEventListener('keydown', this.$el.keydownEvent)
    },
    toggle(value) {
      if (this.readOnly) {
        return
      }

      const oldValue = !!value
      const newValue = !value
      this.$emit('update', newValue, oldValue)
    },
  },
}
</script>
