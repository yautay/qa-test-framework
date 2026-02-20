import { ref } from "vue";
import { Modal } from "bootstrap";

export function useReportNavigation(store, keyHeld, superZoomActive, noteEditorActive) {
  const baseZoom = ref(100);

  function handleKeydown(evt, handlers = {}) {
    const modalEl = document.getElementById("vrtModal");
    const isOpen = modalEl && modalEl.classList.contains("show");

    if (noteEditorActive?.value) {
      return;
    }

    if (!isOpen) {
      handleKeydownNonModal(evt, handlers);
      return;
    }

    if (handlers.promptActive?.()) {
      if (evt.code === "Space") {
        handlers.confirmPrompt?.();
      } else if (evt.code === "ShiftLeft" || evt.code === "ShiftRight") {
        handlers.cancelPrompt?.();
      }
      return;
    }

    const k = evt.key;

    if (["1", "2", "3", "4"].includes(k)) {
      store.setColumns(Number(k));
    } else if (k.toUpperCase() === "A") {
      evt.preventDefault();
      keyHeld.value.a = true;
      store.navigate(-1);
    } else if (k.toUpperCase() === "D") {
      evt.preventDefault();
      keyHeld.value.d = true;
      store.navigate(1);
    } else if (k.toUpperCase() === "W") {
      if (!superZoomActive.value) {
        keyHeld.value.w = true;
        handlers.activateSuperZoom?.();
      }
    } else if (k.toUpperCase() === "S") {
      if (!store.isTagLocked("bug")) {
        handlers.promptTag?.("bug");
      }
    } else if (k.toUpperCase() === "C") {
      if (!store.isTagLocked("aso")) {
        handlers.promptTag?.("aso");
      }
    } else if (k === "\\") {
      if (!store.isTagLocked("baseline")) {
        handlers.promptTag?.("baseline");
      }
    } else if (k.toUpperCase() === "N") {
      handlers.openNoteEditor?.();
    } else if (evt.code === "ShiftLeft" || evt.code === "ShiftRight") {
      handlers.closeModal?.();
    } else if (k === "Escape") {
      const modalEl = document.getElementById("vrtModal");
      if (modalEl) {
        const modal = Modal.getInstance(modalEl);
        modal?.hide();
      }
    }
  }

  function handleKeydownNonModal(evt, handlers = {}) {
    if (noteEditorActive?.value) {
      return;
    }

    if (handlers.promptActive?.()) {
      if (evt.code === "Space") {
        handlers.confirmPrompt?.();
      } else if (evt.code === "ShiftLeft" || evt.code === "ShiftRight") {
        handlers.cancelPrompt?.();
      }
      return;
    }

    const k = evt.key;

    if (evt.code === "ArrowUp") {
      evt.preventDefault();
      store.navigateSelection(-1);
    } else if (evt.code === "ArrowDown") {
      evt.preventDefault();
      store.navigateSelection(1);
    } else if (evt.code === "Space") {
      evt.preventDefault();
      handlers.openSelectedRow?.();
    } else if (evt.code === "ShiftLeft" || evt.code === "ShiftRight") {
      handlers.goToHero?.();
    } else if (k === "Escape") {
      store.selectedIndex = -1;
    }
  }

  function handleKeyup(evt) {
    if (noteEditorActive?.value) {
      return;
    }
    const k = evt.key;
    if (k.toUpperCase() === "A") keyHeld.value.a = false;
    if (k.toUpperCase() === "D") keyHeld.value.d = false;
    if (k.toUpperCase() === "W") {
      keyHeld.value.w = false;
      superZoomActive.value = false;
    }
  }

  function activateSuperZoom() {
    superZoomActive.value = true;
  }

  function deactivateSuperZoom() {
    superZoomActive.value = false;
  }

  function goToHero() {
    window.history.pushState({}, "", "/");
    window.dispatchEvent(new PopStateEvent("popstate"));
  }

  function openSelectedRow() {
    if (store.selectedIndex >= 0 && store.selectedIndex < store.filteredSorted.length) {
      const row = store.filteredSorted[store.selectedIndex];
      handlers?.show?.(row, "test", store.selectedIndex);
    }
  }

  return {
    baseZoom,
    handleKeydown,
    handleKeydownNonModal,
    handleKeyup,
    activateSuperZoom,
    deactivateSuperZoom,
    goToHero,
    openSelectedRow,
  };
}
