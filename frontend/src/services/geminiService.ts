export async function getAIEnvironmentalAdvice(data: any) {
  // Giả lập độ trễ của AI (1.5 giây)
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        status: `Chỉ số AQI ${Math.round(data.aqi)} tại ${data.province_name} đang ở mức ${data.aqi > 100 ? 'ô nhiễm' : 'an toàn'}.`,
        warning: data.aqi > 150 
          ? "Cảnh báo: Ô nhiễm không khí nghiêm trọng, hãy đeo khẩu trang N95 khi ra đường." 
          : "Không có cảnh báo đặc biệt.",
        recommendations: [
          data.aqi > 100 ? "Bật máy lọc không khí ở chế độ cao." : "Mở cửa sổ để không khí lưu thông.",
          data.temperature > 35 ? "Tránh các hoạt động thể lực ngoài trời do nắng nóng." : "Tập thể dục bình thường.",
          "Uống đủ nước và bổ sung vitamin C."
        ]
      });
    }, 1500);
  });
}
