<template>
  <main class="tavern-page" :style="{ backgroundImage: `url(${tavernBg})` }">
    <div class="tavern-shade"></div>
    <div class="tavern-lamp"></div>

    <RouterLink class="tavern-exit" to="/">离开酒馆</RouterLink>
    <div class="tavern-auth" aria-label="账号入口">
      <button class="auth-btn" type="button">登录</button>
      <button class="auth-btn auth-btn--primary" type="button">注册</button>
    </div>

    <p class="tavern-top-title">今晚的门,只为晚归的人开</p>

    <div class="tavern-content">
      <section class="tavern-center" aria-labelledby="tavern-title">
        <p class="tavern-kicker">Midnight Tavern</p>
        <h1 id="tavern-title" class="tavern-title">深夜酒馆</h1>
        <p class="tavern-lead">把烦心事暂时放在吧台,也可以留下一点今天的开心。</p>
        <p class="tavern-sublead">不用急着解释,酒馆会先替你收好。</p>
      </section>

      <section class="message-section" aria-labelledby="message-title">
        <div class="message-head">
          <div>
            <p class="message-kicker">Tonight's Notes</p>
            <h2 id="message-title" class="message-title">漂在城市里的旧酒瓶</h2>
          </div>
          <p class="message-hint">点开一只旧酒瓶,看看卡片背面藏着什么。</p>
        </div>

        <div class="bottle-grid">
          <div v-for="post in tavernPosts" :key="post.id" class="bottle-item">
            <button
              class="bottle-card"
              :class="{ 'bottle-card--open': activePostId === post.id }"
              type="button"
              :aria-expanded="activePostId === post.id"
              @click="togglePost(post.id)"
            >
              <span class="bottle-shape" aria-hidden="true">
                <span class="bottle-neck"></span>
                <span class="bottle-body"></span>
                <span class="bottle-shine"></span>
              </span>
              <span class="bottle-tag">
                <span class="tag-string"></span>
                <span class="tag-line">
                  <span class="tag-author">{{ post.author }}</span>
                  <span class="tag-separator">：</span>
                  <span class="tag-topic">{{ post.topic }}</span>
                </span>
                <span class="tag-action">{{ activePostId === post.id ? '收好瓶塞' : '拆开纸签' }}</span>
              </span>
            </button>

          </div>
        </div>
      </section>
    </div>

    <Transition name="letter-fade">
      <div v-if="selectedPost" class="letter-overlay" @click.self="closePost">
        <article class="letter-modal" role="dialog" aria-modal="true" :aria-labelledby="`letter-title-${selectedPost.id}`">
          <button class="letter-close" type="button" @click="closePost">收回瓶中信</button>
          <p class="letter-kicker">来自:{{ selectedPost.author }}</p>
          <h2 :id="`letter-title-${selectedPost.id}`" class="letter-title">{{ selectedPost.topic }}</h2>
          <div class="letter-body">
            <p>{{ selectedPost.body }}</p>
          </div>
        </article>
      </div>
    </Transition>

    <button class="write-trigger" type="button" @click="composerOpen = true">投下一只瓶子</button>

    <Transition name="composer-fade">
      <div v-if="composerOpen" class="composer-panel" role="dialog" aria-modal="true" aria-label="投下一只瓶子">
        <div class="composer-head">
          <div>
            <p class="composer-kicker">Bottle a note</p>
            <h2 class="composer-title">投下一只瓶子</h2>
          </div>
          <button class="composer-close" type="button" aria-label="关闭" @click="composerOpen = false">×</button>
        </div>
        <p class="composer-copy">未来登录后,这只瓶子会真正漂进酒馆里。现在先作为 UI 预览。</p>
        <label class="composer-field">
          <span>瓶子署名</span>
          <input type="text" placeholder="比如:晚归的人" />
        </label>
        <label class="composer-field">
          <span>瓶身标签</span>
          <input type="text" placeholder="一句话贴在瓶身上" />
        </label>
        <label class="composer-field">
          <span>想封进瓶子里的话</span>
          <textarea rows="5" placeholder="烦心事或开心事,都可以封进这里。"></textarea>
        </label>
        <button class="composer-submit" type="button">封好瓶塞</button>
      </div>
    </Transition>
  </main>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import tavernBg from '@/assets/img/test7.jfif'

/** 深夜酒馆静态留言,后续接入后端后可替换为接口数据 */
interface TavernPost {
  id: string
  author: string
  topic: string
  body: string
}

const activePostId = ref<string | null>(null)
const composerOpen = ref(false)

const tavernPosts: TavernPost[] = [
  {
    id: 'late-bus',
    author: '赶末班车的人',
    topic: '今天差点哭出来',
    body: '忙了一整天,回家的时候才发现自己还没好好吃饭。可是走到楼下,看见便利店还亮着灯,忽然觉得也没有那么糟。',
  },
  {
    id: 'rain-cat',
    author: '躲雨的猫',
    topic: '捡到一点好运气',
    body: '下午下雨的时候有人把伞往我这边偏了一点。只是很小的事,但我记了很久。',
  },
  {
    id: 'old-ticket',
    author: '旧车票',
    topic: '没说出口的话',
    body: '有些话错过那一站就不知道怎么再开口了。今晚先寄存在这里,等我勇敢一点再取走。',
  },
  {
    id: 'warm-window',
    author: '亮着灯的窗',
    topic: '终于做完了',
    body: '拖了很久的事情今天终于收尾。不是很完美,但我第一次觉得自己没有逃走。',
  },
  {
    id: 'quiet-star',
    author: '安静的星星',
    topic: '想睡个好觉',
    body: '希望今晚不要再反复想白天的失误。明天醒来,我想重新开始一次。',
  },
  {
    id: 'soda-memory',
    author: '冰镇汽水',
    topic: '小小开心',
    body: '喜欢的歌随机播放到了,路边的风也刚刚好。虽然只是普通一天,但我想把它记下来。',
  },
  {
    id: 'city-soda',
    author: '冰镇汽水',
    topic: '小小开心',
    body: '喜欢的歌随机播放到了,路边的风也刚刚好。虽然只是普通一天,但我想把它记下来。',
  },
  {
    id: 'midnight-soda',
    author: '冰镇汽水',
    topic: '小小开心',
    body: '喜欢的歌随机播放到了,路边的风也刚刚好。虽然只是普通一天,但我想把它记下来。',
  },
]

const selectedPost = computed(() => tavernPosts.find((post) => post.id === activePostId.value) ?? null)

function togglePost(id: string) {
  activePostId.value = activePostId.value === id ? null : id
}

function closePost() {
  activePostId.value = null
}
</script>

<style scoped>
.tavern-page {
  position: relative;
  min-height: 100vh;
  background-attachment: fixed;
  background-color: #090806;
  background-position: center;
  background-size: cover;
  color: rgba(255, 244, 224, 0.94);
}

.tavern-shade {
  position: fixed;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.36) 34%, rgba(0, 0, 0, 0.84)),
    radial-gradient(circle at 50% 18%, rgba(132, 88, 42, 0.28), transparent 34%);
  pointer-events: none;
}

.tavern-lamp {
  position: fixed;
  top: -14rem;
  left: 50%;
  width: min(46rem, 92vw);
  height: 34rem;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 186, 92, 0.28), rgba(255, 186, 92, 0.08) 42%, transparent 70%);
  pointer-events: none;
  transform: translateX(-50%);
}

.tavern-exit,
.tavern-auth,
.tavern-top-title,
.write-trigger,
.composer-panel {
  z-index: 3;
}

.tavern-exit {
  position: fixed;
  top: 1.4rem;
  left: 1.4rem;
  border: 1px solid rgba(255, 228, 190, 0.22);
  border-radius: 999px;
  padding: 0.62rem 0.95rem;
  background: rgba(8, 7, 6, 0.46);
  color: rgba(255, 240, 218, 0.86);
  font-size: 0.86rem;
  text-decoration: none;
  transition:
    background 0.2s ease,
    transform 0.2s ease;
}

.tavern-exit:hover,
.auth-btn:hover,
.write-trigger:hover,
.composer-submit:hover {
  transform: translateY(-1px);
}

.tavern-exit:hover {
  background: rgba(50, 34, 21, 0.56);
}

.tavern-auth {
  position: fixed;
  top: 1.35rem;
  right: 1.4rem;
  display: flex;
  gap: 0.55rem;
}

.auth-btn,
.write-trigger,
.composer-submit,
.composer-close {
  border: 1px solid rgba(255, 228, 190, 0.22);
  color: rgba(255, 240, 218, 0.9);
  cursor: pointer;
  transition:
    background 0.2s ease,
    transform 0.2s ease,
    border-color 0.2s ease;
}

.auth-btn {
  border-radius: 999px;
  padding: 0.56rem 0.88rem;
  background: rgba(8, 7, 6, 0.42);
}

.auth-btn--primary {
  background: rgba(145, 88, 45, 0.44);
  border-color: rgba(255, 207, 143, 0.34);
}

.tavern-top-title {
  position: fixed;
  top: 1.55rem;
  left: 50%;
  margin: 0;
  color: rgba(255, 228, 190, 0.78);
  font-family: 'Noto Serif SC', 'Songti SC', serif;
  font-size: clamp(0.9rem, 2.2vw, 1.2rem);
  letter-spacing: 0.18em;
  text-align: center;
  text-shadow: 0 6px 24px rgba(0, 0, 0, 0.76);
  transform: translateX(-50%);
  white-space: nowrap;
}

.tavern-content {
  position: relative;
  z-index: 1;
  width: min(100% - 2rem, 92rem);
  margin: 0 auto;
  padding: 8.6rem 0 9rem;
}

.tavern-center {
  width: min(100%, 48rem);
  margin: 0 auto;
  padding: 1rem;
  text-align: center;
  animation: tavernTitleLift 1.45s cubic-bezier(0.2, 0.82, 0.2, 1) both;
  transform: translateY(-3vh);
  will-change: opacity, transform;
}

.tavern-kicker {
  margin: 0 0 1rem;
  color: rgba(255, 191, 112, 0.78);
  font-size: 0.78rem;
  letter-spacing: 0.28em;
  text-transform: uppercase;
}

.tavern-title {
  margin: 0;
  font-family: 'Noto Serif SC', 'Songti SC', serif;
  font-size: clamp(3rem, 10vw, 7rem);
  font-weight: 700;
  letter-spacing: 0.12em;
  line-height: 1;
  text-shadow:
    0 10px 30px rgba(0, 0, 0, 0.72),
    0 0 42px rgba(255, 174, 83, 0.16);
}

.tavern-lead,
.tavern-sublead {
  max-width: 38rem;
  margin: 1.35rem auto 0;
  color: rgba(255, 232, 203, 0.78);
  font-size: clamp(1rem, 2.4vw, 1.22rem);
  line-height: 1.9;
  text-shadow: 0 6px 22px rgba(0, 0, 0, 0.72);
}

.tavern-sublead {
  margin-top: 0.35rem;
  color: rgba(255, 232, 203, 0.62);
  font-size: clamp(0.9rem, 2vw, 1.06rem);
}

.message-section {
  margin-top: clamp(2.8rem, 7vw, 6rem);
}

.message-head {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.2rem;
}

.message-kicker,
.composer-kicker {
  margin: 0 0 0.35rem;
  color: rgba(255, 190, 116, 0.66);
  font-size: 0.72rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.message-title,
.composer-title {
  margin: 0;
  font-family: 'Noto Serif SC', 'Songti SC', serif;
  font-size: clamp(1.35rem, 3vw, 2rem);
}

.message-hint {
  max-width: 22rem;
  margin: 0;
  color: rgba(255, 232, 203, 0.62);
  font-size: 0.9rem;
  line-height: 1.7;
  text-align: right;
}

.bottle-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(12.8rem, 1fr));
  gap: 1.1rem 0.9rem;
  align-items: start;
}

.bottle-item {
  --bottle-tilt: -3deg;
  --bottle-float: 0rem;
  display: grid;
  justify-items: center;
  gap: 0.58rem;
}

.bottle-item:nth-child(5n + 2) {
  --bottle-tilt: 4deg;
  --bottle-float: 0.75rem;
}

.bottle-item:nth-child(5n + 3) {
  --bottle-tilt: -1deg;
  --bottle-float: 0.35rem;
}

.bottle-item:nth-child(5n + 4) {
  --bottle-tilt: 5deg;
  --bottle-float: -0.2rem;
}

.bottle-item:nth-child(5n) {
  --bottle-tilt: -5deg;
  --bottle-float: 0.5rem;
}

.bottle-card {
  position: relative;
  display: flex;
  align-items: end;
  justify-content: center;
  width: 100%;
  min-height: 15.5rem;
  border: 0;
  padding: 0 0.4rem 0.8rem;
  background: transparent;
  color: rgba(255, 240, 218, 0.9);
  cursor: pointer;
  text-align: center;
  transform: translateY(var(--bottle-float)) rotate(var(--bottle-tilt));
  transition:
    filter 0.24s ease,
    transform 0.24s ease;
}

.bottle-card:hover,
.bottle-card--open {
  filter: drop-shadow(0 18px 24px rgba(0, 0, 0, 0.34));
  transform: translateY(calc(var(--bottle-float) - 0.25rem)) rotate(var(--bottle-tilt));
}

.bottle-card--open .bottle-tag {
  transform: translate(-50%, 0.55rem) rotate(-1deg);
}

.bottle-shape {
  position: absolute;
  inset: 0.2rem 2.5rem 1.1rem;
}

.bottle-neck {
  position: absolute;
  top: 0;
  left: 50%;
  width: 2.9rem;
  height: 4.6rem;
  border: 1px solid rgba(229, 166, 98, 0.22);
  border-bottom: 0;
  border-radius: 0.8rem 0.8rem 0.28rem 0.28rem;
  background:
    linear-gradient(90deg, rgba(255, 206, 139, 0.12), transparent 28%, rgba(0, 0, 0, 0.16) 72%),
    linear-gradient(180deg, rgba(86, 49, 22, 0.7), rgba(41, 25, 16, 0.86));
  box-shadow: inset 0 0 14px rgba(255, 190, 112, 0.08);
  transform: translateX(-50%);
}

.bottle-neck::before {
  position: absolute;
  top: -0.44rem;
  left: 50%;
  width: 3.25rem;
  height: 0.72rem;
  border: 1px solid rgba(229, 166, 98, 0.28);
  border-radius: 999px;
  background: rgba(51, 30, 18, 0.92);
  content: '';
  transform: translateX(-50%);
}

.bottle-body {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  height: 11.6rem;
  border: 1px solid rgba(229, 166, 98, 0.23);
  border-radius: 4.8rem 4.8rem 2.2rem 2.2rem / 3.2rem 3.2rem 2rem 2rem;
  background:
    radial-gradient(circle at 30% 18%, rgba(255, 209, 137, 0.18), transparent 28%),
    linear-gradient(110deg, rgba(255, 198, 120, 0.12), transparent 22%, rgba(0, 0, 0, 0.28) 74%),
    linear-gradient(180deg, rgba(91, 47, 20, 0.74), rgba(36, 22, 16, 0.94));
  box-shadow:
    inset 0 0 28px rgba(255, 179, 92, 0.08),
    inset -18px -8px 24px rgba(0, 0, 0, 0.22),
    0 22px 36px rgba(0, 0, 0, 0.32);
}

.bottle-shine {
  position: absolute;
  top: 4.4rem;
  left: 24%;
  width: 1rem;
  height: 6.5rem;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(255, 229, 181, 0.22), transparent);
  opacity: 0.62;
  transform: rotate(8deg);
}

.bottle-tag {
  position: absolute;
  bottom: 2.15rem;
  left: 50%;
  width: min(11rem, 82%);
  border: 1px solid rgba(118, 75, 42, 0.34);
  border-radius: 0.58rem;
  padding: 0.78rem 0.72rem 0.62rem;
  background:
    linear-gradient(135deg, rgba(255, 243, 213, 0.94), rgba(206, 174, 121, 0.92)),
    #e7c98f;
  color: rgba(62, 41, 25, 0.9);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.42),
    0 12px 20px rgba(0, 0, 0, 0.24);
  transform: translateX(-50%) rotate(2deg);
  transform-origin: top center;
  transition: transform 0.24s ease;
}

.tag-string {
  position: absolute;
  top: -2.6rem;
  left: 50%;
  width: 1px;
  height: 2.75rem;
  background: rgba(224, 194, 145, 0.62);
  transform: translateX(-50%) rotate(-4deg);
}

.tag-line {
  display: flex;
  align-items: center;
  min-width: 0;
}

.tag-author {
  color: rgba(82, 48, 26, 0.8);
  flex: 0 0 auto;
  font-size: 0.82rem;
  letter-spacing: 0.04em;
}

.tag-separator {
  color: rgba(82, 48, 26, 0.56);
  flex: 0 0 auto;
}

.tag-topic {
  overflow: hidden;
  color: rgba(55, 34, 22, 0.92);
  font-size: 0.9rem;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tag-action {
  display: inline-flex;
  margin-top: 0.42rem;
  border-top: 1px solid rgba(91, 57, 32, 0.18);
  padding-top: 0.36rem;
  color: rgba(76, 45, 25, 0.58);
  font-size: 0.72rem;
}

.letter-overlay {
  position: fixed;
  inset: 0;
  z-index: 5;
  display: grid;
  place-items: center;
  padding: 1.2rem;
  background: rgba(7, 5, 4, 0.56);
}

.letter-modal {
  position: relative;
  width: min(42rem, 92vw);
  max-height: 76vh;
  overflow: hidden;
  border: 1px solid rgba(116, 75, 42, 0.34);
  border-radius: 1.2rem;
  padding: clamp(1.4rem, 4vw, 2.2rem);
  background:
    radial-gradient(circle at 16% 10%, rgba(255, 255, 255, 0.34), transparent 22%),
    linear-gradient(135deg, rgba(255, 244, 217, 0.96), rgba(207, 174, 117, 0.94)),
    #e4c68e;
  color: rgba(61, 40, 24, 0.9);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.45),
    0 32px 90px rgba(0, 0, 0, 0.48);
}

.letter-modal::before {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(72, 43, 22, 0.06) 1px, transparent 1px),
    linear-gradient(180deg, rgba(72, 43, 22, 0.04) 1px, transparent 1px);
  background-size: 2.4rem 2.4rem;
  content: '';
  pointer-events: none;
}

.letter-close {
  position: absolute;
  top: 1rem;
  right: 1rem;
  z-index: 1;
  border: 1px solid rgba(86, 52, 28, 0.2);
  border-radius: 999px;
  padding: 0.42rem 0.72rem;
  background: rgba(255, 249, 231, 0.42);
  color: rgba(72, 43, 22, 0.78);
  cursor: pointer;
  font-size: 0.78rem;
}

.letter-kicker {
  position: relative;
  margin: 0 0 0.7rem;
  color: rgba(99, 59, 31, 0.62);
  font-size: 0.82rem;
  letter-spacing: 0.08em;
}

.letter-title {
  position: relative;
  margin: 0;
  padding-right: 7rem;
  font-family: 'Noto Serif SC', 'Songti SC', serif;
  font-size: clamp(1.6rem, 5vw, 2.7rem);
  line-height: 1.2;
}

.letter-body {
  position: relative;
  max-height: min(42vh, 24rem);
  overflow-y: auto;
  margin-top: 1.2rem;
  padding-right: 0.35rem;
  color: rgba(58, 38, 24, 0.82);
  font-size: clamp(1rem, 2.2vw, 1.12rem);
  line-height: 2;
}

.letter-body p {
  margin: 0;
}

.letter-fade-enter-active,
.letter-fade-leave-active {
  transition: opacity 0.24s ease;
}

.letter-fade-enter-active .letter-modal,
.letter-fade-leave-active .letter-modal {
  transition: transform 0.24s ease, opacity 0.24s ease;
}

.letter-fade-enter-from,
.letter-fade-leave-to {
  opacity: 0;
}

.letter-fade-enter-from .letter-modal,
.letter-fade-leave-to .letter-modal {
  opacity: 0;
  transform: translateY(12px) scale(0.97) rotate(-1deg);
}

.write-trigger {
  position: fixed;
  right: 1.5rem;
  bottom: 1.5rem;
  border-radius: 999px;
  padding: 0.8rem 1.1rem;
  background: rgba(145, 88, 45, 0.5);
  border-color: rgba(255, 207, 143, 0.36);
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.34);
}

.composer-panel {
  position: fixed;
  right: 1.5rem;
  bottom: 5.2rem;
  width: min(25rem, calc(100vw - 2rem));
  border: 1px solid rgba(255, 224, 184, 0.18);
  border-radius: 1.6rem;
  padding: 1.1rem;
  background: rgba(13, 11, 12, 0.76);
  color: rgba(255, 240, 218, 0.9);
  box-shadow: 0 28px 76px rgba(0, 0, 0, 0.42);
}

.composer-head {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 1rem;
}

.composer-close {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.06);
  font-size: 1.2rem;
  line-height: 1;
}

.composer-copy {
  margin: 0.85rem 0 1rem;
  color: rgba(255, 232, 203, 0.62);
  font-size: 0.9rem;
  line-height: 1.7;
}

.composer-field {
  display: grid;
  gap: 0.42rem;
  margin-top: 0.74rem;
  color: rgba(255, 211, 156, 0.74);
  font-size: 0.82rem;
}

.composer-field input,
.composer-field textarea {
  width: 100%;
  border: 1px solid rgba(255, 224, 184, 0.16);
  border-radius: 1rem;
  padding: 0.72rem 0.8rem;
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 244, 224, 0.92);
  outline: none;
  resize: vertical;
}

.composer-field input::placeholder,
.composer-field textarea::placeholder {
  color: rgba(255, 232, 203, 0.36);
}

.composer-submit {
  width: 100%;
  margin-top: 1rem;
  border-radius: 999px;
  padding: 0.72rem 1rem;
  background: rgba(145, 88, 45, 0.5);
}

.composer-fade-enter-active,
.composer-fade-leave-active {
  transition: opacity 0.24s ease, transform 0.24s ease;
}

.composer-fade-enter-from,
.composer-fade-leave-to {
  opacity: 0;
  transform: translateY(10px) scale(0.98);
}

@keyframes tavernTitleLift {
  0% {
    opacity: 0;
    transform: translateY(12vh) scale(0.98);
    filter: blur(8px);
  }

  38% {
    opacity: 1;
    filter: blur(0);
  }

  100% {
    opacity: 1;
    transform: translateY(-3vh) scale(1);
    filter: blur(0);
  }
}

@media (max-width: 760px) {
  .tavern-page {
    background-attachment: scroll;
  }

  .tavern-exit {
    top: 1rem;
    left: 1rem;
  }

  .tavern-auth {
    top: 1rem;
    right: 1rem;
  }

  .auth-btn {
    padding: 0.5rem 0.72rem;
  }

  .tavern-top-title {
    position: absolute;
    top: 4.6rem;
    width: calc(100% - 2rem);
    white-space: normal;
  }

  .tavern-content {
    padding-top: 9.8rem;
  }

  .tavern-center {
    transform: translateY(0);
    animation-name: tavernTitleLiftMobile;
  }

  .message-head {
    align-items: start;
    flex-direction: column;
  }

  .message-hint {
    text-align: left;
  }

  .composer-panel {
    right: 1rem;
    bottom: 4.8rem;
  }

  .letter-modal {
    max-height: 82vh;
    padding: 1.35rem;
  }

  .letter-title {
    padding-right: 0;
    padding-top: 1.8rem;
  }

  .letter-body {
    max-height: 50vh;
  }

  .write-trigger {
    right: 1rem;
    bottom: 1rem;
  }
}

@keyframes tavernTitleLiftMobile {
  0% {
    opacity: 0;
    transform: translateY(8vh) scale(0.98);
    filter: blur(8px);
  }

  38% {
    opacity: 1;
    filter: blur(0);
  }

  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
    filter: blur(0);
  }
}
</style>
