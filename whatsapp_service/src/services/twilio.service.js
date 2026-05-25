// const twilio = require('twilio');

// const client = twilio(
//     process.env.TWILIO_ACCOUNT_SID,
//     process.env.TWILIO_AUTH_TOKEN
// );

// class TwilioService {
    
//     // Send absence alert
//     static async sendAbsenceAlert(phone, studentName, date) {
//         try {
//             const message = await client.messages.create({
//                 body: `📚 *EduVision Attendance Alert*\n\nDear ${studentName},\n\nYou were marked *ABSENT* on ${date}.\n\nPlease reply with reason:\n_REASON: [your reason]_\n\nExample: REASON: Fever`,
//                 from: `whatsapp:${process.env.TWILIO_PHONE_NUMBER}`,
//                 to: `whatsapp:${phone}`
//             });
            
//             console.log(`✅ Alert sent to ${phone}: ${message.sid}`);
//             return { success: true, messageId: message.sid };
//         } catch (error) {
//             console.error(`❌ Failed to send to ${phone}:`, error.message);
//             return { success: false, error: error.message };
//         }
//     }
    
//     // Send monthly report
//     static async sendMonthlyReport(phone, studentName, stats) {
//         try {
//             const { total_days, present_days, percentage, days_needed } = stats;
            
//             const statusEmoji = percentage >= 75 ? '✅' : '⚠️';
//             const statusText = percentage >= 75 ? 'Good Standing' : 'Below Required';
            
//             const body = `📊 *Monthly Attendance Report*\n\n` +
//                         `👤 *${studentName}*\n` +
//                         `📅 Total Days: ${total_days}\n` +
//                         `✅ Present: ${present_days}\n` +
//                         `❌ Absent: ${total_days - present_days}\n` +
//                         `📈 Percentage: ${percentage}%\n` +
//                         `📌 Status: ${statusEmoji} ${statusText}\n\n` +
//                         (days_needed > 0 ? `⚠️ Need *${days_needed}* more days to reach 75%` : `🎉 Keep up the good work!`);
            
//             const message = await client.messages.create({
//                 body: body,
//                 from: `whatsapp:${process.env.TWILIO_PHONE_NUMBER}`,
//                 to: `whatsapp:${phone}`
//             });
            
//             console.log(`✅ Monthly report sent to ${phone}`);
//             return { success: true, messageId: message.sid };
//         } catch (error) {
//             console.error(`❌ Failed to send report to ${phone}:`, error.message);
//             return { success: false, error: error.message };
//         }
//     }
    
//     // Send parent alert (below 60%)
//     static async sendParentAlert(parentPhone, studentName, percentage) {
//         try {
//             const message = await client.messages.create({
//                 body: `⚠️ *EduVision Parent Alert*\n\nYour child *${studentName}* has attendance below 60% (${percentage}%).\n\nPlease encourage regular attendance.\n\n- EduVision Team`,
//                 from: `whatsapp:${process.env.TWILIO_PHONE_NUMBER}`,
//                 to: `whatsapp:${parentPhone}`
//             });
            
//             return { success: true, messageId: message.sid };
//         } catch (error) {
//             return { success: false, error: error.message };
//         }
//     }
// }

// module.exports = TwilioService;