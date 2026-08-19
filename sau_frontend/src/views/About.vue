<template>
  <div class="about">
    <el-card class="about-card">
      <div class="about-header">
        <h1>Hệ thống Tự động hóa Mạng xã hội</h1>
        <p class="version">social-auto-upload (Phiên bản tiếng Việt)</p>
      </div>

      <el-divider />

      <div class="about-section">
        <h3>Giới thiệu hệ thống</h3>
        <p>
          Hệ thống là công cụ tự động hóa mạnh mẽ giúp các nhà sáng tạo nội dung và nhà phát triển phân phối video/ảnh đồng thời lên nhiều nền tảng mạng xã hội lớn trong nước và quốc tế chỉ với 1 cú nhấp chuột.
          Hỗ trợ đăng video, đăng bài viết hình ảnh, quản lý đa tài khoản và hẹn giờ đăng thông minh.
        </p>
      </div>

      <div class="about-section">
        <h3>Các nền tảng hỗ trợ</h3>
        <div class="platform-tags">
          <el-tag type="primary">Facebook (Reels & Fanpage)</el-tag>
          <el-tag type="danger">Instagram (Reels & Post)</el-tag>
          <el-tag type="success">TikTok Quốc tế</el-tag>
          <el-tag type="danger">YouTube Studio</el-tag>
          <el-tag type="success">Threads (Meta)</el-tag>
          <el-tag type="info">Twitter / X</el-tag>
          <el-tag type="danger">Pinterest (Video Pin)</el-tag>
          <el-tag type="primary">Zalo Video / OA</el-tag>
        </div>
      </div>

      <div class="about-section">
        <h3>Tính năng nổi bật</h3>
        <ul class="feature-list">
          <li>Quản lý nhiều tài khoản & duy trì trạng thái đăng nhập, Cookie</li>
          <li>Tải lên, lưu trữ và xem trước thư viện tư liệu video/ảnh</li>
          <li>Đăng bài đa nền tảng một chạm</li>
          <li>Hẹn giờ đăng bài tự động và đăng hàng loạt theo lịch trình</li>
          <li>Nhập / Xuất dữ liệu Cookie tiện lợi</li>
        </ul>
      </div>

      <div class="about-section">
        <h3>Công nghệ sử dụng</h3>
        <div class="tech-tags">
          <el-tag effect="plain">Vue 3</el-tag>
          <el-tag effect="plain">Element Plus (Vi)</el-tag>
          <el-tag effect="plain">Pinia</el-tag>
          <el-tag effect="plain">Flask Async</el-tag>
          <el-tag effect="plain">Patchright / Playwright</el-tag>
          <el-tag effect="plain">SQLite</el-tag>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
// 关于页面组件
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.about {
  max-width: 700px;
  margin: 0 auto;

  .about-card {
    .about-header {
      text-align: center;

      h1 {
        color: $text-primary;
        margin: 0 0 8px 0;
        font-size: 24px;
      }

      .version {
        color: $text-secondary;
        font-size: 14px;
        margin: 0;
      }
    }

    .about-section {
      margin-bottom: 24px;

      h3 {
        font-size: 16px;
        color: $text-primary;
        margin: 0 0 12px 0;
      }

      p {
        color: $text-secondary;
        line-height: 1.8;
        margin: 0;
      }

      .platform-tags,
      .tech-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }

      .feature-list {
        margin: 0;
        padding-left: 20px;
        color: $text-secondary;
        line-height: 2;
      }
    }
  }
}
</style>
