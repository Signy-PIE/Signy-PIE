<template>
  <div class="word-block">
    <div class="word-title">{{ word.string }}</div>
  </div>
</template>
<script setup lang="ts">
import type { Word } from "@/types/word"

defineProps<{
  word: Word
}>()
</script>
<style scoped>
.word-block {
  width: 85%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  padding: 15px;
  border: 3px solid var(--color-darkpurple);
  border-radius: 20px;

  .word-title {
    font-size: 18px;
    font-weight: bold;
    color: var(--color-darkpurple);
  }
}
</style>
