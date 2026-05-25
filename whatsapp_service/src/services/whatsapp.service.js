const axios = require('axios');
const twilio = require('twilio');

// WhatsApp Cloud API config
const WHATSAPP_API = 'https://graph.facebook.com/v18.0';
const PHONE_NUMBER_ID = process.env.WHATSAPP_PHONE_ID;
const ACCESS_TOKEN = process.env.WHATSAPP_TOKEN;

// Twilio config
const twilioClient = process.env.TWILIO_ACCOUNT_SID && process.env.TWILIO_AUTH_TOKEN 
  ? twilio(process.env.TWILIO_ACCOUNT_SID, process.env.TWILIO_AUTH_TOKEN) 
  : null;

class WhatsAppService {
  
  // ==================== PRIMARY: WhatsApp Cloud API (FREE) ====================
  static async sendViaCloudAPI(phone, message) {
    if (!PHONE_NUMBER_ID || !ACCESS_TOKEN) {
      return { success: false, method: 'cloud_api', error: 'Not configured' };
    }
    
    try {
      const cleanPhone = phone.replace(/[^0-9]/g, '');
      
      const res = await axios.post(
        `${WHATSAPP_API}/${PHONE_NUMBER_ID}/messages`,
        {
          messaging_product: "whatsapp",
          to: cleanPhone,
          type: "text",
          text: { body: message }
        },
        {
          headers: {
            'Authorization': `Bearer ${ACCESS_TOKEN}`,
            'Content-Type': 'application/json'
          },
          timeout: 10000
        }
      );
      
      console.log(`✅ [Cloud API] Sent to ${cleanPhone}: ${res.data.messages?.[0]?.id}`);
      return { success: true, method: 'cloud_api', id: res.data.messages?.[0]?.id };
    } catch (error) {
      const errMsg = error.response?.data?.error?.message || error.message;
      console.log(`⚠️ [Cloud API] Failed for ${phone}: ${errMsg}`);
      return { success: false, method: 'cloud_api', error: errMsg };
    }
  }
  
  // ==================== BACKUP: Twilio ====================
  static async sendViaTwilio(phone, message) {
    if (!twilioClient) {
      return { success: false, method: 'twilio', error: 'Not configured' };
    }
    
    try {
      const res = await twilioClient.messages.create({
        body: message,
        from: `whatsapp:${process.env.TWILIO_PHONE_NUMBER}`,
        to: `whatsapp:${phone}`
      });
      
      console.log(`✅ [Twilio] Sent to ${phone}: ${res.sid}`);
      return { success: true, method: 'twilio', id: res.sid };
    } catch (error) {
      console.log(`⚠️ [Twilio] Failed for ${phone}: ${error.message}`);
      return { success: false, method: 'twilio', error: error.message };
    }
  }
  
  // ==================== SMART SEND ====================
  static async sendMessage(phone, message) {
    if (!phone) {
      console.log('⚠️ No phone number provided');
      return { success: false, error: 'No phone number' };
    }
    
    console.log(`📤 Sending to ${phone}...`);
    
    // Try Cloud API first (FREE)
    if (PHONE_NUMBER_ID && ACCESS_TOKEN) {
      const result = await WhatsAppService.sendViaCloudAPI(phone, message);
      if (result.success) return result;
      console.log('   ↪ Falling back to Twilio...');
    }
    
    // Fallback to Twilio
    if (twilioClient) {
      const result = await WhatsAppService.sendViaTwilio(phone, message);
      if (result.success) return result;
    }
    
    console.log('❌ All methods failed');
    return { success: false, error: 'All WhatsApp services failed' };
  }
  
  // ==================== ALERT TEMPLATES ====================
  static async sendAbsenceAlert(phone, studentName, date) {
    const message = `📚 *EduVision Attendance Alert*\n\n` +
                   `Dear ${studentName},\n\n` +
                   `You were marked *ABSENT* on ${date}.\n\n` +
                   `Please reply with reason:\n` +
                   `REASON: [your reason]\n\n` +
                   `_Thank you_`;
    
    return await WhatsAppService.sendMessage(phone, message);
  }
  
  static async sendMonthlyReport(phone, studentName, stats) {
    const { total_days, present_days, percentage, days_needed } = stats;
    const emoji = percentage >= 75 ? '✅' : '⚠️';
    
    let message = `📊 *Monthly Attendance Report*\n\n` +
                  `👤 ${studentName}\n` +
                  `📅 Total: ${total_days || 0} days\n` +
                  `✅ Present: ${present_days || 0} days\n` +
                  `❌ Absent: ${(total_days || 0) - (present_days || 0)} days\n` +
                  `📈 ${percentage || 0}%\n\n` +
                  `${emoji} Status: ${percentage >= 75 ? 'Good Standing' : 'Below Required'}`;
    
    if (days_needed > 0) {
      message += `\n⚠️ Need *${days_needed}* more days to reach 75%`;
    }
    
    return await WhatsAppService.sendMessage(phone, message);
  }
}

module.exports = WhatsAppService;