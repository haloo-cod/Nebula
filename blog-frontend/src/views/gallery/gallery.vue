<template>
  <PageBackground>
    <div class="relative flex flex-col items-center justify-start pt-24 md:pt-0 w-full">
      <div class="panels-wrapper">
        <div class="panels-container md:flex md:gap-6">
          <div class="sticky-panel w-full md:w-[22%] flex-shrink-0">
            <div class="flex flex-col gap-6">
              <ProfilePanel
                :avatar="avatar"
                :name="profile.name"
                :bio="profile.bio"
                :links="socialLinks"
                square
                flat
              />
              <PlaceholderPanel class="hidden md:flex" flat />
            </div>
          </div>

          <div class="w-full md:w-[56%] flex-shrink-0">
            <RouterView />
          </div>

          <div class="sticky-panel hidden md:block w-full md:w-[22%] flex-shrink-0">
            <div class="flex flex-col gap-6">
              <CalendarPanel flat />
              <PostStatsChart flat />
            </div>
          </div>
        </div>
      </div>
    </div>
  </PageBackground>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import PageBackground from '@/components/PageBackground.vue'
import ProfilePanel from '@/components/panels/ProfilePanel.vue'
import PlaceholderPanel from '@/components/panels/PlaceholderPanel.vue'
import CalendarPanel from '@/components/panels/CalendarPanel.vue'
import PostStatsChart from '@/components/panels/PostStatsChart.vue'
import { avatar, profile, socialLinks } from '@/data/profile'
</script>

<style scoped>
.panels-wrapper {
  position: relative;
  z-index: 10;
  width: 100%;
  margin-left: auto;
  margin-right: auto;
  margin-top: 4rem;
  max-width: 96rem;
  padding-left: 0.25rem;
  padding-right: 0.25rem;
}

@media (min-width: 768px) {
  .panels-wrapper {
    margin-top: 100px;
  }

  .sticky-panel {
    position: sticky;
    top: 100px;
    align-self: flex-start;
  }
}
</style>
