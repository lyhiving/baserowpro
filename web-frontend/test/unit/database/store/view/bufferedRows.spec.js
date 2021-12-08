import bufferedRows from '@baserow/modules/database/store/view/bufferedRows'
import { TestApp } from '@baserow/test/helpers/testApp'
import { ContainsViewFilterType } from '@baserow/modules/database/viewFilters'

describe('Buffered rows view store helper', () => {
  let testApp = null
  let store = null

  beforeEach(() => {
    testApp = new TestApp()
    store = testApp.store
  })

  afterEach(() => {
    testApp.afterEach()
  })

  // test('visibleRows', async () => {
  //   // A test client that has 100 rows from id 1 through 100. It returns the
  //   // requested rows they are available.
  //   const service = () => {
  //     return {
  //       fetchRows({ viewId, limit = 100, offset = null }) {
  //         const all = Array(14)
  //           .fill(null)
  //           .map((row, index) => {
  //             return { id: index + 1 }
  //           })
  //
  //         const data = {
  //           results: all.slice(offset, offset + limit),
  //         }
  //         return { data }
  //       },
  //     }
  //   }
  //   const populateRow = (row) => {
  //     row._ = {}
  //     return row
  //   }
  //   const testStore = bufferedRows({ service, populateRow })
  //
  //   const state = Object.assign(testStore.state(), {
  //     visible: [0, 0],
  //     requestSize: 4,
  //     viewId: 1,
  //     rows: [
  //       { id: 1 },
  //       { id: 2 },
  //       null,
  //       null,
  //       null,
  //       null,
  //       null,
  //       null,
  //       null,
  //       null,
  //       null,
  //       null,
  //       null,
  //       null,
  //       null,
  //     ],
  //   })
  //   testStore.state = () => state
  //   store.registerModule('test', testStore)
  //
  //   await store.dispatch('test/visibleRows', { startIndex: 0, endIndex: 1 })
  //   const rowsInStore = store.getters['test/getRows']
  //   expect(rowsInStore[0].id).toBe(1)
  //   expect(rowsInStore[1].id).toBe(2)
  //   expect(rowsInStore[2]).toBe(null)
  //   expect(rowsInStore[3]).toBe(null)
  //   expect(rowsInStore[4]).toBe(null)
  //   expect(rowsInStore[5]).toBe(null)
  //   expect(rowsInStore[6]).toBe(null)
  //   expect(rowsInStore[7]).toBe(null)
  //   expect(rowsInStore[8]).toBe(null)
  //   expect(rowsInStore[9]).toBe(null)
  //   expect(rowsInStore[10]).toBe(null)
  //   expect(rowsInStore[11]).toBe(null)
  //   expect(rowsInStore[12]).toBe(null)
  //   expect(rowsInStore[13]).toBe(null)
  //
  //   await store.dispatch('test/visibleRows', { startIndex: 1, endIndex: 2 })
  //   expect(rowsInStore[0].id).toBe(1)
  //   expect(rowsInStore[1].id).toBe(2)
  //   expect(rowsInStore[2].id).toBe(3)
  //   expect(rowsInStore[3].id).toBe(4)
  //   expect(rowsInStore[4].id).toBe(5)
  //   expect(rowsInStore[5].id).toBe(6)
  //   expect(rowsInStore[6]).toBe(null)
  //   expect(rowsInStore[7]).toBe(null)
  //   expect(rowsInStore[8]).toBe(null)
  //   expect(rowsInStore[9]).toBe(null)
  //   expect(rowsInStore[10]).toBe(null)
  //   expect(rowsInStore[11]).toBe(null)
  //   expect(rowsInStore[12]).toBe(null)
  //   expect(rowsInStore[13]).toBe(null)
  //
  //   await store.dispatch('test/visibleRows', { startIndex: 10, endIndex: 11 })
  //   expect(rowsInStore[0].id).toBe(1)
  //   expect(rowsInStore[1].id).toBe(2)
  //   expect(rowsInStore[2].id).toBe(3)
  //   expect(rowsInStore[3].id).toBe(4)
  //   expect(rowsInStore[4].id).toBe(5)
  //   expect(rowsInStore[5].id).toBe(6)
  //   expect(rowsInStore[6]).toBe(null)
  //   expect(rowsInStore[7]).toBe(null)
  //   expect(rowsInStore[8]).toBe(null)
  //   expect(rowsInStore[9].id).toBe(10)
  //   expect(rowsInStore[10].id).toBe(11)
  //   expect(rowsInStore[11].id).toBe(12)
  //   expect(rowsInStore[12].id).toBe(13)
  //   expect(rowsInStore[13]).toBe(null)
  //
  //   await store.dispatch('test/visibleRows', { startIndex: 8, endIndex: 11 })
  //   expect(rowsInStore[0].id).toBe(1)
  //   expect(rowsInStore[1].id).toBe(2)
  //   expect(rowsInStore[2].id).toBe(3)
  //   expect(rowsInStore[3].id).toBe(4)
  //   expect(rowsInStore[4].id).toBe(5)
  //   expect(rowsInStore[5].id).toBe(6)
  //   expect(rowsInStore[6].id).toBe(7)
  //   expect(rowsInStore[7].id).toBe(8)
  //   expect(rowsInStore[8].id).toBe(9)
  //   expect(rowsInStore[9].id).toBe(10)
  //   expect(rowsInStore[10].id).toBe(11)
  //   expect(rowsInStore[11].id).toBe(12)
  //   expect(rowsInStore[12].id).toBe(13)
  //   expect(rowsInStore[13]).toBe(null)
  //
  //   store.state.test.rows[12]._ = { tmp: true }
  //   await store.dispatch('test/visibleRows', { startIndex: 12, endIndex: 14 })
  //   expect(rowsInStore[0].id).toBe(1)
  //   expect(rowsInStore[1].id).toBe(2)
  //   expect(rowsInStore[2].id).toBe(3)
  //   expect(rowsInStore[3].id).toBe(4)
  //   expect(rowsInStore[4].id).toBe(5)
  //   expect(rowsInStore[5].id).toBe(6)
  //   expect(rowsInStore[6].id).toBe(7)
  //   expect(rowsInStore[7].id).toBe(8)
  //   expect(rowsInStore[8].id).toBe(9)
  //   expect(rowsInStore[9].id).toBe(10)
  //   expect(rowsInStore[10].id).toBe(11)
  //   expect(rowsInStore[11].id).toBe(12)
  //   expect(rowsInStore[12].id).toBe(13)
  //   // Check if the state has not been overwritten.
  //   expect(rowsInStore[12]._.tmp).toBe(true)
  //   expect(rowsInStore[13].id).toBe(14)
  // })
  //
  // test('refresh', async () => {
  //   const service = () => {
  //     return {
  //       fetchRows({ viewId, limit = 100, offset = null }) {
  //         const all = Array(30)
  //           .fill(null)
  //           .map((row, index) => {
  //             return { id: index + 1 }
  //           })
  //
  //         const data = {
  //           results: all.slice(offset, offset + limit),
  //         }
  //         return { data }
  //       },
  //       fetchCount() {
  //         const data = { count: 30 }
  //         return { data }
  //       },
  //     }
  //   }
  //   const populateRow = (row) => {
  //     row._ = {}
  //     return row
  //   }
  //   const testStore = bufferedRows({ service, populateRow })
  //
  //   const state = Object.assign(testStore.state(), {
  //     visible: [10, 13],
  //     requestSize: 8,
  //     viewId: 1,
  //     rows: [
  //       { id: 1 },
  //       { id: 2 },
  //       { id: 3 },
  //       { id: 4 },
  //       { id: 5 },
  //       { id: 6 },
  //       { id: 7 },
  //       { id: 8 },
  //       { id: 9 },
  //       { id: 10 },
  //       { id: 11 },
  //       { id: 12 },
  //       { id: 13 },
  //       { id: 14 },
  //       { id: 15 },
  //       { id: 16 },
  //       { id: 17 },
  //       { id: 18 },
  //       { id: 19 },
  //       { id: 20 },
  //     ],
  //   })
  //   testStore.state = () => state
  //   store.registerModule('test', testStore)
  //
  //   await store.dispatch('test/refresh', {})
  //   const rowsInStore = store.getters['test/getRows']
  //   expect(rowsInStore[0]).toBe(null)
  //   expect(rowsInStore[1]).toBe(null)
  //   expect(rowsInStore[2]).toBe(null)
  //   expect(rowsInStore[3]).toBe(null)
  //   expect(rowsInStore[4]).toBe(null)
  //   expect(rowsInStore[5]).toBe(null)
  //   expect(rowsInStore[6]).toBe(null)
  //   expect(rowsInStore[7]).toBe(null)
  //   expect(rowsInStore[8].id).toBe(9)
  //   expect(rowsInStore[9].id).toBe(10)
  //   expect(rowsInStore[10].id).toBe(11)
  //   expect(rowsInStore[11].id).toBe(12)
  //   expect(rowsInStore[12].id).toBe(13)
  //   expect(rowsInStore[13].id).toBe(14)
  //   expect(rowsInStore[14].id).toBe(15)
  //   expect(rowsInStore[15].id).toBe(16)
  //   expect(rowsInStore[16]).toBe(null)
  //   expect(rowsInStore[17]).toBe(null)
  //   expect(rowsInStore[18]).toBe(null)
  //   expect(rowsInStore[19]).toBe(null)
  // })
  //
  // test('refresh with less', async () => {
  //   const service = () => {
  //     return {
  //       fetchRows({ viewId, limit = 100, offset = null }) {
  //         const all = Array(10)
  //           .fill(null)
  //           .map((row, index) => {
  //             return { id: index + 1 }
  //           })
  //
  //         const data = {
  //           results: all.slice(offset, offset + limit),
  //         }
  //         return { data }
  //       },
  //       fetchCount() {
  //         const data = { count: 10 }
  //         return { data }
  //       },
  //     }
  //   }
  //   const populateRow = (row) => {
  //     row._ = {}
  //     return row
  //   }
  //   const testStore = bufferedRows({ service, populateRow })
  //
  //   const state = Object.assign(testStore.state(), {
  //     visible: [9, 12],
  //     requestSize: 8,
  //     viewId: 1,
  //     rows: [
  //       { id: 1 },
  //       { id: 2 },
  //       { id: 3 },
  //       { id: 4 },
  //       { id: 5 },
  //       { id: 6 },
  //       { id: 7 },
  //       { id: 8 },
  //       { id: 9 },
  //       { id: 10 },
  //       { id: 11 },
  //       { id: 12 },
  //       { id: 13 },
  //       { id: 14 },
  //       { id: 15 },
  //       { id: 16 },
  //       { id: 17 },
  //       { id: 18 },
  //       { id: 19 },
  //       { id: 20 },
  //     ],
  //   })
  //   testStore.state = () => state
  //   store.registerModule('test', testStore)
  //
  //   await store.dispatch('test/refresh', {})
  //   const rowsInStore = store.getters['test/getRows']
  //   expect(rowsInStore[0]).toBe(null)
  //   expect(rowsInStore[1]).toBe(null)
  //   expect(rowsInStore[2].id).toBe(3)
  //   expect(rowsInStore[3].id).toBe(4)
  //   expect(rowsInStore[4].id).toBe(5)
  //   expect(rowsInStore[5].id).toBe(6)
  //   expect(rowsInStore[6].id).toBe(7)
  //   expect(rowsInStore[7].id).toBe(8)
  //   expect(rowsInStore[8].id).toBe(9)
  //   expect(rowsInStore[9].id).toBe(10)
  // })
  //
  // test('refresh to empty', async () => {
  //   const service = () => {
  //     return {
  //       fetchRows({ viewId, limit = 100, offset = null }) {
  //         return { data: { results: [] } }
  //       },
  //       fetchCount() {
  //         return { data: { count: 0 } }
  //       },
  //     }
  //   }
  //   const populateRow = (row) => {
  //     row._ = {}
  //     return row
  //   }
  //   const testStore = bufferedRows({ service, populateRow })
  //
  //   const state = Object.assign(testStore.state(), {
  //     visible: [0, 1],
  //     requestSize: 2,
  //     viewId: 1,
  //     rows: [{ id: 1 }, { id: 2 }, null, null],
  //   })
  //   testStore.state = () => state
  //   store.registerModule('test', testStore)
  //
  //   await store.dispatch('test/refresh', {})
  //   expect(store.getters['test/getRows'].length).toBe(0)
  //   expect(store.getters['test/getVisible']).toStrictEqual([0, 0])
  // })
  //
  // test('test row matches filters', async () => {
  //   const view = {
  //     id: 1,
  //     filters_disabled: false,
  //     filter_type: 'AND',
  //     filters: [
  //       {
  //         id: 1,
  //         view: 1,
  //         field: 1,
  //         type: ContainsViewFilterType.getType(),
  //         value: 'value',
  //       },
  //     ],
  //     sortings: [],
  //   }
  //   const fields = []
  //   const primary = {
  //     id: 1,
  //     name: 'Test 1',
  //     type: 'text',
  //     primary: true,
  //   }
  //
  //   const testStore = bufferedRows({ service: null, populateRow: null })
  //   store.registerModule('test', testStore)
  //
  //   expect(
  //     await store.dispatch('test/rowMatchesFilters', {
  //       view,
  //       fields,
  //       primary,
  //       row: { id: 12, order: '12.00000000000000000000', field_1: 'Value 12' },
  //     })
  //   ).toBe(true)
  //   expect(
  //     await store.dispatch('test/rowMatchesFilters', {
  //       view,
  //       fields,
  //       primary,
  //       row: {
  //         id: 12,
  //         order: '12.00000000000000000000',
  //         field_1: 'Not matching 12',
  //       },
  //     })
  //   ).toBe(false)
  //   expect(
  //     await store.dispatch('test/rowMatchesFilters', {
  //       view,
  //       fields,
  //       primary,
  //       row: {
  //         id: 12,
  //         order: '12.00000000000000000000',
  //         field_1: 'Not matching 12',
  //       },
  //       overrides: { field_1: 'Value' },
  //     })
  //   ).toBe(true)
  //   view.filters_disabled = true
  //   expect(
  //     await store.dispatch('test/rowMatchesFilters', {
  //       view,
  //       fields,
  //       primary,
  //       row: {
  //         id: 12,
  //         order: '12.00000000000000000000',
  //         field_1: 'Not matching 12',
  //       },
  //     })
  //   ).toBe(true)
  // })

  test('test created new row', async () => {
    const view = {
      id: 1,
      filters_disabled: false,
      filter_type: 'AND',
      filters: [],
      sortings: [],
    }
    const fields = []
    const primary = {
      id: 1,
      name: 'Test 1',
      type: 'text',
      primary: true,
    }
    const populateRow = (row) => {
      row._ = {}
      return row
    }

    const testStore = bufferedRows({ service: null, populateRow })
    const state = Object.assign(testStore.state(), {
      visible: [0, 0],
      requestSize: 4,
      viewId: 1,
      rows: [
        null,
        { id: 3, order: '3.00000000000000000000', field_1: 'Row 3' },
        { id: 5, order: '5.00000000000000000000', field_1: 'Row 5' },
        { id: 6, order: '6.00000000000000000000', field_1: 'Row 6' },
        { id: 7, order: '7.00000000000000000000', field_1: 'Row 7' },
        null,
        { id: 10, order: '10.00000000000000000000', field_1: 'Row 10' },
        { id: 11, order: '11.00000000000000000000', field_1: 'Row 11' },
        { id: 12, order: '12.00000000000000000000', field_1: 'Row 12' },
        { id: 14, order: '14.00000000000000000000', field_1: 'Row 14' },
        null,
      ],
    })
    testStore.state = () => state
    store.registerModule('test', testStore)

    await store.dispatch('test/createdNewRow', {
      view,
      fields,
      primary,
      values: {
        id: 2,
        order: '2.00000000000000000000',
        field_1: 'Row 2',
      },
    })
    let rowsInStore = store.getters['test/getRows']
    expect(rowsInStore[0]).toBe(null)
    // This is the newly created row. We couldn't be 100% sure this was the right
    // position, so it's added as null.
    expect(rowsInStore[1]).toBe(null)
    expect(rowsInStore[2].id).toBe(3)
    expect(rowsInStore[3].id).toBe(5)
    expect(rowsInStore[4].id).toBe(6)
    expect(rowsInStore[5].id).toBe(7)
    expect(rowsInStore[6]).toBe(null)
    expect(rowsInStore[7].id).toBe(10)
    expect(rowsInStore[8].id).toBe(11)
    expect(rowsInStore[9].id).toBe(12)
    expect(rowsInStore[10].id).toBe(14)
    expect(rowsInStore[11]).toBe(null)

    await store.dispatch('test/createdNewRow', {
      view,
      fields,
      primary,
      values: {
        id: 4,
        order: '4.00000000000000000000',
        field_1: 'Row 4',
      },
    })
    rowsInStore = store.getters['test/getRows']
    expect(rowsInStore[0]).toBe(null)
    expect(rowsInStore[1]).toBe(null)
    expect(rowsInStore[2].id).toBe(3)
    // This is the newly created row. Because there was one before and after, we
    // were 100% sure the row was supposed to be at this position.
    expect(rowsInStore[3].id).toBe(4)
    expect(rowsInStore[4].id).toBe(5)
    expect(rowsInStore[5].id).toBe(6)
    expect(rowsInStore[6].id).toBe(7)
    expect(rowsInStore[7]).toBe(null)
    expect(rowsInStore[8].id).toBe(10)
    expect(rowsInStore[9].id).toBe(11)
    expect(rowsInStore[10].id).toBe(12)
    expect(rowsInStore[11].id).toBe(14)
    expect(rowsInStore[12]).toBe(null)

    await store.dispatch('test/createdNewRow', {
      view,
      fields,
      primary,
      values: {
        id: 13,
        order: '13.00000000000000000000',
        field_1: 'Row 13',
      },
    })
    rowsInStore = store.getters['test/getRows']
    expect(rowsInStore[0]).toBe(null)
    expect(rowsInStore[1]).toBe(null)
    expect(rowsInStore[2].id).toBe(3)
    expect(rowsInStore[3].id).toBe(4)
    expect(rowsInStore[4].id).toBe(5)
    expect(rowsInStore[5].id).toBe(6)
    expect(rowsInStore[6].id).toBe(7)
    expect(rowsInStore[7]).toBe(null)
    expect(rowsInStore[8].id).toBe(10)
    expect(rowsInStore[9].id).toBe(11)
    expect(rowsInStore[10].id).toBe(12)
    // We again know for sure the row was supposed to be at this position.
    expect(rowsInStore[11].id).toBe(13)
    expect(rowsInStore[12].id).toBe(14)
    expect(rowsInStore[13]).toBe(null)

    await store.dispatch('test/createdNewRow', {
      view,
      fields,
      primary,
      values: {
        id: 16,
        order: '16.00000000000000000000',
        field_1: 'Row 16',
      },
    })
    rowsInStore = store.getters['test/getRows']
    expect(rowsInStore[0]).toBe(null)
    expect(rowsInStore[1]).toBe(null)
    expect(rowsInStore[2].id).toBe(3)
    expect(rowsInStore[3].id).toBe(4)
    expect(rowsInStore[4].id).toBe(5)
    expect(rowsInStore[5].id).toBe(6)
    expect(rowsInStore[6].id).toBe(7)
    expect(rowsInStore[7]).toBe(null)
    expect(rowsInStore[8].id).toBe(10)
    expect(rowsInStore[9].id).toBe(11)
    expect(rowsInStore[10].id).toBe(12)
    expect(rowsInStore[11].id).toBe(13)
    expect(rowsInStore[12].id).toBe(14)
    expect(rowsInStore[13]).toBe(null)
    // We didn't know for sure that this was the last row, so it had to be added as
    // null.
    expect(rowsInStore[14]).toBe(null)

    store.getters['test/getRows'][14] = {
      id: 16,
      order: '16.00000000000000000000',
      field_1: 'Row 16',
    }
    await store.dispatch('test/createdNewRow', {
      view,
      fields,
      primary,
      values: {
        id: 17,
        order: '17.00000000000000000000',
        field_1: 'Row 17',
      },
    })
    expect(rowsInStore[0]).toBe(null)
    expect(rowsInStore[1]).toBe(null)
    expect(rowsInStore[2].id).toBe(3)
    expect(rowsInStore[3].id).toBe(4)
    expect(rowsInStore[4].id).toBe(5)
    expect(rowsInStore[5].id).toBe(6)
    expect(rowsInStore[6].id).toBe(7)
    expect(rowsInStore[7]).toBe(null)
    expect(rowsInStore[8].id).toBe(10)
    expect(rowsInStore[9].id).toBe(11)
    expect(rowsInStore[10].id).toBe(12)
    expect(rowsInStore[11].id).toBe(13)
    expect(rowsInStore[12].id).toBe(14)
    expect(rowsInStore[13]).toBe(null)
    expect(rowsInStore[14].id).toBe(16)
    // Because we've made id 16 known and it was the last item, we do know for sure
    // where 17 belonged.
    expect(rowsInStore[15].id).toBe(17)

    store.getters['test/getRows'][0] = {
      id: 1,
      order: '1.00000000000000000000',
      field_1: 'Row 1',
    }
    await store.dispatch('test/createdNewRow', {
      view,
      fields,
      primary,
      values: {
        id: 0,
        order: '0.00000000000000000000',
        field_1: 'Row 0',
      },
    })
    // Because we've made first row known, we know for sure if one needs to be
    // placed first.
    expect(rowsInStore[0].id).toBe(0)
    expect(rowsInStore[1].id).toBe(1)
    expect(rowsInStore[2]).toBe(null)
    expect(rowsInStore[3].id).toBe(3)
    expect(rowsInStore[4].id).toBe(4)
    expect(rowsInStore[5].id).toBe(5)
    expect(rowsInStore[6].id).toBe(6)
    expect(rowsInStore[7].id).toBe(7)
    expect(rowsInStore[8]).toBe(null)
    expect(rowsInStore[9].id).toBe(10)
    expect(rowsInStore[10].id).toBe(11)
    expect(rowsInStore[11].id).toBe(12)
    expect(rowsInStore[12].id).toBe(13)
    expect(rowsInStore[13].id).toBe(14)
    expect(rowsInStore[14]).toBe(null)
    expect(rowsInStore[15].id).toBe(16)
    expect(rowsInStore[16].id).toBe(17)
  })

  test('test deleted new row', async () => {
    const view = {
      id: 1,
      filters_disabled: false,
      filter_type: 'AND',
      filters: [],
      sortings: [],
    }
    const fields = []
    const primary = {
      id: 1,
      name: 'Test 1',
      type: 'text',
      primary: true,
    }
    const populateRow = (row) => {
      row._ = {}
      return row
    }

    const testStore = bufferedRows({ service: null, populateRow })
    const state = Object.assign(testStore.state(), {
      visible: [0, 0],
      requestSize: 4,
      viewId: 1,
      rows: [
        null,
        { id: 3, order: '3.00000000000000000000', field_1: 'Row 3' },
        { id: 5, order: '5.00000000000000000000', field_1: 'Row 5' },
        { id: 6, order: '6.00000000000000000000', field_1: 'Row 6' },
        { id: 7, order: '7.00000000000000000000', field_1: 'Row 7' },
        null,
        null,
        null,
        { id: 11, order: '11.00000000000000000000', field_1: 'Row 11' },
        { id: 12, order: '12.00000000000000000000', field_1: 'Row 12' },
        { id: 14, order: '14.00000000000000000000', field_1: 'Row 14' },
        null,
      ],
    })
    testStore.state = () => state
    store.registerModule('test', testStore)

    await store.dispatch('test/deletedExistingRow', {
      view,
      fields,
      primary,
      row: {
        id: 1,
        order: '1.00000000000000000000',
        field_1: 'Row 1',
      },
    })
    const rowsInStore = store.getters['test/getRows']
    expect(rowsInStore[0].id).toBe(3)
    expect(rowsInStore[1].id).toBe(5)
    expect(rowsInStore[2].id).toBe(6)
    expect(rowsInStore[3].id).toBe(7)
    expect(rowsInStore[4]).toBe(null)
    expect(rowsInStore[5]).toBe(null)
    expect(rowsInStore[6]).toBe(null)
    expect(rowsInStore[7].id).toBe(11)
    expect(rowsInStore[8].id).toBe(12)
    expect(rowsInStore[9].id).toBe(14)
    expect(rowsInStore[10]).toBe(null)

    await store.dispatch('test/deletedExistingRow', {
      view,
      fields,
      primary,
      row: {
        id: 15,
        order: '15.00000000000000000000',
        field_1: 'Row 15',
      },
    })
    expect(rowsInStore[0].id).toBe(3)
    expect(rowsInStore[1].id).toBe(5)
    expect(rowsInStore[2].id).toBe(6)
    expect(rowsInStore[3].id).toBe(7)
    expect(rowsInStore[4]).toBe(null)
    expect(rowsInStore[5]).toBe(null)
    expect(rowsInStore[6]).toBe(null)
    expect(rowsInStore[7].id).toBe(11)
    expect(rowsInStore[8].id).toBe(12)
    expect(rowsInStore[9].id).toBe(14)

    await store.dispatch('test/deletedExistingRow', {
      view,
      fields,
      primary,
      row: {
        id: 9,
        order: '9.00000000000000000000',
        field_1: 'Row 9',
      },
    })
    expect(rowsInStore[0].id).toBe(3)
    expect(rowsInStore[1].id).toBe(5)
    expect(rowsInStore[2].id).toBe(6)
    expect(rowsInStore[3].id).toBe(7)
    expect(rowsInStore[4]).toBe(null)
    expect(rowsInStore[5]).toBe(null)
    expect(rowsInStore[6].id).toBe(11)
    expect(rowsInStore[7].id).toBe(12)
    expect(rowsInStore[8].id).toBe(14)

    await store.dispatch('test/deletedExistingRow', {
      view,
      fields,
      primary,
      row: {
        id: 5,
        order: '5.00000000000000000000',
        field_1: 'Row 5',
      },
    })
    expect(rowsInStore[0].id).toBe(3)
    expect(rowsInStore[1].id).toBe(6)
    expect(rowsInStore[2].id).toBe(7)
    expect(rowsInStore[3]).toBe(null)
    expect(rowsInStore[4]).toBe(null)
    expect(rowsInStore[5].id).toBe(11)
    expect(rowsInStore[6].id).toBe(12)
    expect(rowsInStore[7].id).toBe(14)

    await store.dispatch('test/deletedExistingRow', {
      view,
      fields,
      primary,
      row: {
        id: 14,
        order: '14.00000000000000000000',
        field_1: 'Row 14',
      },
    })
    expect(rowsInStore[0].id).toBe(3)
    expect(rowsInStore[1].id).toBe(6)
    expect(rowsInStore[2].id).toBe(7)
    expect(rowsInStore[3]).toBe(null)
    expect(rowsInStore[4]).toBe(null)
    expect(rowsInStore[5].id).toBe(11)
    expect(rowsInStore[6].id).toBe(12)
  })
})