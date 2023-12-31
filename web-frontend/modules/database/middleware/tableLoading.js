/**
 * Middleware that changes the table loading state to true before the route
 * changes. That way we can show a loading animation to the user when switching
 * between views.
 */
export default async function ({ route, from, store }) {
  function parseIntOrNull(x) {
    return x != null ? parseInt(x) : null
  }

  if (
    !from ||
    parseIntOrNull(route.params.tableId) !==
      parseIntOrNull(from.params.tableId) ||
    parseIntOrNull(route.params.viewId) !== parseIntOrNull(from.params.viewId)
  ) {
    await store.dispatch('table/setLoading', true)
  }
}
