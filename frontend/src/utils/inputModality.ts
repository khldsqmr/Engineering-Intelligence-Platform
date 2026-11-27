document.addEventListener(
  'pointerdown',
  () => {
    document.documentElement.dataset.inputModality = 'pointer'
  },
  true,
)

document.addEventListener(
  'keydown',
  event => {
    if (
      !event.metaKey &&
      !event.ctrlKey &&
      !event.altKey
    ) {
      document.documentElement.dataset.inputModality = 'keyboard'
    }
  },
  true,
)
