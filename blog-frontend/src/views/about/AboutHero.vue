<template>
  <div class="about-hero">
    <!-- 封面图 -->
    <div class="hero-cover">
      <img :src="coverImage" alt="About Cover" class="hero-cover-img" />
    </div>

    <!-- 头像 + 个人信息 -->
    <div class="hero-profile">
      <img :src="avatar" alt="avatar" class="hero-avatar" />

      <div class="hero-info">
        <div class="hero-text">
          <h1 class="hero-name">关于我</h1>
          <p class="hero-subtitle">Hello World, I'm {{ profile.name }}</p>
        </div>

        <!-- 社交链接 -->
        <div class="hero-socials">
          <a
            v-for="link in socialLinks"
            :key="link.label"
            :href="link.url"
            :aria-label="link.label"
            class="social-link"
            target="_blank"
            rel="noopener noreferrer"
          >
            <SvgIcon :name="link.icon" class="social-icon" />
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import SvgIcon from '@/components/SvgIcon.vue'
import { avatar, coverImage, profile, socialLinks } from '@/data/profile'
</script>

<style scoped>
.about-hero {
  position: relative;
}

.hero-cover {
  position: relative;
  width: auto;
  height: 21rem;
  overflow: hidden;
  margin: 1rem 1rem 0;
  border-radius: 1.5rem;
}

.hero-cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.8s ease;
}

.hero-cover:hover .hero-cover-img {
  transform: scale(1.05);
}

.hero-profile {
  display: flex;
  align-items: flex-end;
  gap: 1.25rem;
  padding: 0 1.5rem;
  margin-top: 1.5rem;
  position: relative;
  z-index: 2;
}

.hero-avatar {
  width: 5.5rem;
  height: 5.5rem;
  border-radius: 50%;
  border: 3px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  object-fit: cover;
  flex-shrink: 0;
}

.hero-info {
  flex: 1;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 0.25rem;
}

.hero-text {
  min-width: 0;
}

.hero-name {
  margin: 0;
  color: var(--text-primary);
  font-size: 1.8rem;
  font-weight: 800;
  letter-spacing: 0.02em;
}

.hero-subtitle {
  margin: 0.2rem 0 0;
  color: rgba(140, 185, 255, 0.85);
  font-size: 0.82rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.hero-socials {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}

.social-link {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.2rem;
  height: 2.2rem;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: var(--text-secondary);
  transition: all 0.2s ease;
}

.social-link:hover {
  background: rgba(140, 185, 255, 0.15);
  border-color: rgba(140, 185, 255, 0.4);
  color: rgba(180, 210, 255, 0.95);
  transform: translateY(-2px);
}

.social-icon {
  width: 1.1rem;
  height: 1.1rem;
}

@media (max-width: 767px) {
  .hero-cover {
    height: 13rem;
  }

  .hero-profile {
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 0.75rem;
  }

  .hero-avatar {
    width: 4.5rem;
    height: 4.5rem;
  }

  .hero-info {
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
  }

  .hero-name {
    font-size: 1.5rem;
  }
}
</style>
