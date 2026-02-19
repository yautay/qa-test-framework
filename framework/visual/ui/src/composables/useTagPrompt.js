import { ref } from "vue";

export function useTagPrompt() {
  const prompt = ref({ active: false, type: null });

  function promptTag(type) {
    if (prompt.value.active) return;
    if (noteEditor?.value?.active) return;
    if (type === "bug" || type === "aso") {
      if (store?.isTagReported(type)) return;
    }
    if (store?.isTagLocked(type)) return;
    prompt.value = { active: true, type };
  }

  function promptRemoveTag(type) {
    if (prompt.value.active) return;
    if (noteEditor?.value?.active) return;
    if (store?.isTagReported(type)) return;
    prompt.value = { active: true, type: `remove-${type}` };
  }

  async function confirmPrompt(executeSendReport) {
    if (!prompt.value.active) return;
    if (prompt.value.type === "send-report") {
      prompt.value = { active: false, type: null };
      if (executeSendReport) {
        await executeSendReport();
      }
      return;
    }
    const type = prompt.value.type?.replace("remove-", "");
    if (prompt.value.type.startsWith("remove-")) {
      store?.removeTag(type);
      persistTags?.();
    } else {
      store?.toggleTag(type);
      persistTags?.();
    }
    prompt.value = { active: false, type: null };
  }

  function cancelPrompt() {
    if (!prompt.value.active) return;
    prompt.value = { active: false, type: null };
  }

  function isPromptActive() {
    return prompt.value.active;
  }

  function getPromptType() {
    return prompt.value.type;
  }

  return {
    prompt,
    promptTag,
    promptRemoveTag,
    confirmPrompt,
    cancelPrompt,
    isPromptActive,
    getPromptType,
  };
}
