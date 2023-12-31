<template>
  <form @submit.prevent @keydown.enter.prevent>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('tableElementForm.dataSource') }}
      </label>
      <div class="control__elements">
        <Dropdown v-model="values.data_source_id" :show-search="false">
          <DropdownItem
            v-for="dataSource in availableDataSources"
            :key="dataSource.id"
            :name="dataSource.name"
            :value="dataSource.id"
          />
        </Dropdown>
      </div>
    </FormElement>
    <FormInput
      v-model="values.items_per_page"
      :label="$t('tableElementForm.itemsPerPage')"
      :placeholder="$t('tableElementForm.itemsPerPagePlaceholder')"
      :to-value="(value) => parseInt(value)"
      :error="
        $v.values.items_per_page.$dirty && !$v.values.items_per_page.required
          ? $t('error.requiredField')
          : !$v.values.items_per_page.integer
          ? $t('error.integerField')
          : !$v.values.items_per_page.minValue
          ? $t('error.minValueField', { min: 1 })
          : !$v.values.items_per_page.maxValue
          ? $t('error.maxValueField', { max: maxItemPerPage })
          : ''
      "
      type="number"
      @blur="$v.values.items_per_page.$touch()"
    ></FormInput>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('tableElementForm.fields') }}
      </label>
      <div>
        <Expandable
          v-for="(field, index) in values.fields"
          :key="field.id"
          v-sortable="{
            id: field.id,
            update: orderFields,
            handle: '[data-sortable-handle]',
          }"
          class="table-element-form__field"
        >
          <template #header="{ toggle, expanded }">
            <div class="table-element-form__field-header" @click.stop="toggle">
              <div
                class="table-element-form__field-handle"
                data-sortable-handle
              />
              <div class="table-element-form__field-name">{{ field.name }}</div>
              <i
                class="fas"
                :class="
                  expanded
                    ? 'iconoir-nav-arrow-down'
                    : 'iconoir-nav-arrow-right'
                "
              />
            </div>
          </template>
          <template #default>
            <FormInput
              v-model="field.name"
              class="table-element-form__field-label"
              label="Name"
              horizontal
              :error="
                !$v.values.fields.$each[index].name.required
                  ? $t('error.requiredField')
                  : !$v.values.fields.$each[index].name.maxLength
                  ? $t('error.maxLength', { max: 255 })
                  : ''
              "
            >
              <template v-if="values.fields.length > 1" #after-input>
                <Button
                  icon="iconoir-bin"
                  type="light"
                  @click="removeField(field)"
                />
              </template>
            </FormInput>
            <ApplicationBuilderFormulaInputGroup
              v-model="field.value"
              :label="$t('tableElementForm.fieldValueLabel')"
              :placeholder="$t('tableElementForm.fieldValuePlaceholder')"
              :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
              :application-context-additions="{
                element,
              }"
              horizontal
            />
          </template>
        </Expandable>
      </div>
      <Button
        class="table-element-form__add-field"
        prepend-icon="baserow-icon-plus"
        type="link"
        size="tiny"
        @click="addField"
      >
        {{ $t('tableElementForm.addField') }}
      </Button>
    </FormElement>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import { DATA_PROVIDERS_ALLOWED_ELEMENTS } from '@baserow/modules/builder/enums'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'
import {
  getNextAvailableNameInSequence,
  uuid,
} from '@baserow/modules/core/utils/string'
import {
  required,
  maxLength,
  integer,
  minValue,
  maxValue,
} from 'vuelidate/lib/validators'
import { mapGetters } from 'vuex'

export default {
  name: 'TableElementForm',
  components: { ApplicationBuilderFormulaInputGroup },
  mixins: [form],
  inject: ['page'],
  data() {
    return {
      allowedValues: ['data_source_id', 'fields', 'items_per_page'],
      values: {
        data_source_id: null,
        items_per_page: 1,
        fields: [],
      },
    }
  },
  computed: {
    dataSources() {
      return this.$store.getters['dataSource/getPageDataSources'](this.page)
    },
    availableDataSources() {
      return this.dataSources.filter(
        (dataSource) =>
          dataSource.type &&
          this.$registry.get('service', dataSource.type).returnsList
      )
    },
    selectedDataSource() {
      if (!this.values.data_source_id) {
        return null
      }
      return this.$store.getters['dataSource/getPageDataSourceById'](
        this.page,
        this.values.data_source_id
      )
    },
    selectedDataSourceType() {
      if (!this.selectedDataSource || !this.selectedDataSource.type) {
        return null
      }
      return this.$registry.get('service', this.selectedDataSource.type)
    },
    maxItemPerPage() {
      if (!this.selectedDataSourceType) {
        return 20
      }
      return this.selectedDataSourceType.maxResultLimit
    },
    DATA_PROVIDERS_ALLOWED_ELEMENTS() {
      return DATA_PROVIDERS_ALLOWED_ELEMENTS
    },
    ...mapGetters({
      element: 'element/getSelected',
    }),
  },
  watch: {
    'dataSources.length'(newValue, oldValue) {
      if (this.values.data_source_id && oldValue > newValue) {
        if (
          !this.dataSources.some(({ id }) => id === this.values.data_source_id)
        ) {
          // Remove the data_source_id if the related dataSource has been deleted.
          this.values.data_source_id = null
        }
      }
    },
  },
  methods: {
    addField() {
      this.values.fields.push({
        name: getNextAvailableNameInSequence(
          this.$t('tableElementForm.fieldDefaultName'),
          this.values.fields.map(({ name }) => name)
        ),
        value: '',
        id: uuid(), // Temporary id
      })
    },
    removeField(field) {
      this.values.fields = this.values.fields.filter((item) => item !== field)
    },
    orderFields(newOrder) {
      const fieldById = Object.fromEntries(
        this.values.fields.map((field) => [field.id, field])
      )
      this.values.fields = newOrder.map((fieldId) => fieldById[fieldId])
    },
  },
  validations() {
    return {
      values: {
        fields: {
          $each: {
            name: {
              required,
              maxLength: maxLength(225),
            },
          },
        },
        items_per_page: {
          required,
          integer,
          minValue: minValue(1),
          maxValue: maxValue(this.maxItemPerPage),
        },
      },
    }
  },
}
</script>
