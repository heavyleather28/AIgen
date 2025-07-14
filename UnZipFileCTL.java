/*     */ package tw.com.pot.main;
/*     */ 
/*     */ import java.io.File;
/*     */ import java.io.FileInputStream;
/*     */ import java.io.FileNotFoundException;
/*     */ import java.io.IOException;
/*     */ import java.io.UnsupportedEncodingException;
/*     */ import java.util.Properties;
/*     */ import org.apache.commons.lang3.StringUtils;
/*     */ import org.apache.logging.log4j.LogManager;
/*     */ import org.apache.logging.log4j.Logger;
/*     */ import tw.com.pot.TIPS.Password.TIPSPassword;
/*     */ import tw.com.pot.util.ZipUtil;
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ public class UnZipFileCTL
/*     */ {
/*  26 */   private static final Logger logger = LogManager.getLogger(UnZipFileCTL.class);
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private static Properties props;
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private static File sourceFolder;
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static void main(String[] args) {
/*  44 */     logger.info("Program start!");
/*     */     
/*     */     try {
/*  47 */       if (isInit()) {
/*  48 */         if (sourceFolder.exists()) {
/*  49 */           if (sourceFolder.isDirectory()) {
/*     */ 
/*     */             
/*  52 */             processSourceFolder();
/*     */           }
/*     */           else {
/*     */             
/*  56 */             logger.error("指定的 sourceFolder：" + sourceFolder + " 不是目錄型態！");
/*     */           } 
/*     */         } else {
/*  59 */           logger.error("指定的 sourceFolder：" + sourceFolder + " 不存在！");
/*     */         }
/*     */       
/*     */       }
/*  63 */     } catch (Exception exception) {}
/*     */ 
/*     */     
/*  66 */     logger.info("Program end!");
/*  67 */     logger.info("－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－－");
/*  68 */     System.exit(0);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private static boolean isInit() throws Exception {
/*  76 */     props = new Properties();
/*     */     try {
/*  78 */       logger.info("props.load...");
/*  79 */       props.load(new FileInputStream("UnZipFileCTLConfig.properties"));
/*  80 */       logger.info("props.load...OK!");
/*     */ 
/*     */       
/*  83 */       sourceFolder = new File(getProperty("sourceFolder"));
/*     */ 
/*     */     
/*     */     }
/*  87 */     catch (FileNotFoundException e) {
/*  88 */       logger.error("找不到設定檔 UnZipFileCTLConfig.properties！");
/*  89 */       logger.error(e);
/*  90 */       return false;
/*  91 */     } catch (IOException e) {
/*  92 */       logger.error("讀取設定檔 UnZipFileCTLConfig.properties 發生錯誤！");
/*  93 */       logger.error(e);
/*  94 */       return false;
/*     */     } 
/*     */     
/*  97 */     return true;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private static String getProperty(String key) throws UnsupportedEncodingException {
/* 106 */     if (StringUtils.isBlank(props.getProperty(key))) {
/* 107 */       logger.error("Properties檔 參數名稱： " + key + " 不存在，請確認內容是否有誤。");
/*     */     }
/* 109 */     return props.getProperty(key);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private static void processSourceFolder() throws Exception {
/* 118 */     logger.info("processSourceFolder.....");
/*     */     
/* 120 */     File[] sourceFileList = sourceFolder.listFiles();
/* 121 */     for (int i = 0; i < sourceFileList.length; i++) {
/*     */       
/* 123 */       if (sourceFileList[i].isFile()) {
/*     */ 
/*     */ 
/*     */         
/* 127 */         String sourceFileName = sourceFileList[i].getName();
/*     */         
/* 129 */         if (sourceFileName.indexOf(".") >= 20) {
/*     */ 
/*     */           
/* 132 */           String EnStr = 
/* 133 */             sourceFileName.substring(sourceFileName.indexOf(".") - 20, sourceFileName.indexOf("."));
/*     */ 
/*     */           
/* 136 */           TIPSPassword Twd = new TIPSPassword();
/* 137 */           String zipPWD = Twd.genPassword(EnStr);
/*     */ 
/*     */           
/* 140 */           ZipUtil.unzipToFolder(String.valueOf(getProperty("sourceFolder")) + File.separator + sourceFileName, 
/* 141 */               getProperty("archFolder"), zipPWD);
/* 142 */           logger.info("檔案 " + getProperty("sourceFolder") + File.separator + sourceFileName + "已解壓縮。");
/*     */ 
/*     */ 
/*     */ 
/*     */           
/* 147 */           if (sourceFileList[i].delete()) {
/* 148 */             logger.info("檔案 " + sourceFileList[i] + " 已刪除。");
/*     */           } else {
/* 150 */             logger.error("檔案 " + sourceFileList[i] + " 刪除失敗！");
/*     */           } 
/*     */         } 
/*     */       } 
/*     */     } 
/*     */   }
/*     */ }


/* Location:              D:\test\xxx\精誠解壓縮\UnZipFileCTL.jar!\tw\com\pot\main\UnZipFileCTL.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */