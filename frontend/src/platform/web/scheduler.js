// Browser timer adapter; feature hooks depend on these functions instead of window.
export const scheduleTask = (callback, delayMs) => window.setTimeout(callback, delayMs)
export const cancelScheduledTask = (taskId) => window.clearTimeout(taskId)
