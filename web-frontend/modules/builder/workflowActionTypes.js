import { WorkflowActionType } from '@baserow/modules/core/workflowActionTypes'
import NotificationWorkflowActionForm from '@baserow/modules/builder/components/workflowAction/NotificationWorkflowActionForm.vue'
import OpenPageWorkflowActionForm from '@baserow/modules/builder/components/workflowAction/OpenPageWorkflowActionForm'
import CreateRowWorkflowActionForm from '@baserow/modules/builder/components/workflowAction/CreateRowWorkflowActionForm'
import UpdateRowWorkflowActionForm from '@baserow/modules/builder/components/workflowAction/UpdateRowWorkflowActionForm'

export class NotificationWorkflowActionType extends WorkflowActionType {
  static getType() {
    return 'notification'
  }

  get form() {
    return NotificationWorkflowActionForm
  }

  get label() {
    return this.app.i18n.t('workflowActionTypes.notificationLabel')
  }

  execute({ workflowAction: { title, description }, resolveFormula }) {
    return this.app.store.dispatch('toast/info', {
      title: resolveFormula(title),
      message: resolveFormula(description),
    })
  }
}

export class OpenPageWorkflowActionType extends WorkflowActionType {
  static getType() {
    return 'open_page'
  }

  get form() {
    return OpenPageWorkflowActionForm
  }

  get label() {
    return this.app.i18n.t('workflowActionTypes.openPageLabel')
  }

  execute({
    workflowAction: { url },
    applicationContext: { builder, mode },
    resolveFormula,
  }) {
    let urlParsed = resolveFormula(url)

    if (urlParsed.startsWith('/')) {
      if (mode === 'preview') {
        urlParsed = `/builder/${builder.id}/preview${urlParsed}`
      }
      return this.app.router.push(urlParsed)
    }

    if (!urlParsed.startsWith('http')) {
      urlParsed = `https://${urlParsed}`
    }

    window.location.replace(urlParsed)
  }
}

export class CreateRowWorkflowActionType extends WorkflowActionType {
  static getType() {
    return 'create_row'
  }

  get form() {
    return CreateRowWorkflowActionForm
  }

  get label() {
    return this.app.i18n.t('workflowActionTypes.createRowLabel')
  }

  execute({ workflowAction: { id }, resolveFormula }) {
    return this.app.store.dispatch('workflowAction/dispatchAction', {
      workflowActionId: id,
    })
  }
}

export class UpdateRowWorkflowActionType extends WorkflowActionType {
  static getType() {
    return 'update_row'
  }

  get form() {
    return UpdateRowWorkflowActionForm
  }

  get label() {
    return this.app.i18n.t('workflowActionTypes.updateRowLabel')
  }

  execute({ workflowAction: { id }, resolveFormula }) {
    return this.app.store.dispatch('workflowAction/dispatchAction', {
      workflowActionId: id,
    })
  }
}
