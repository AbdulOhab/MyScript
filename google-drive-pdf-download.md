# How to Download Protected/View-Only Files from Google Drive

This method allows you to download view-only or protected PDF files from Google Drive by capturing the rendered images and converting them back into a PDF.

## Step-by-Step Instructions

1. **Open the file in Firefox**

   - Make sure you're in the preview mode

2. **Open Developer Console**

   - **Chrome/Firefox**: Press `Ctrl+Shift+J` (Windows/Linux) or `Option+⌘+J` (Mac)
   - **Or Try Enable pasting in your browser**: Right-click in console & write → "Allow Paste"

3. **Navigate to the Console tab**

   - In the developer tools window, click on the "Console" tab

4. **Paste and execute the JavaScript code**  
   [code link](/google-drive-pdf-download.js)<br>
   Copy and paste the following code into the console, then press Enter:

```javascript
let jspdf = document.createElement('script');
jspdf.onload = function () {
  let pdf = new jsPDF();
  let elements = document.getElementsByTagName('img');
  for (let i in elements) {
    let img = elements[i];
    if (!/^blob:/.test(img.src)) {
      continue;
    }
    let canvasElement = document.createElement('canvas');
    let con = canvasElement.getContext('2d');
    canvasElement.width = img.width;
    canvasElement.height = img.height;
    con.drawImage(img, 0, 0, img.width, img.height);
    let imgData = canvasElement.toDataURL('image/jpeg', 1.0);
    pdf.addImage(imgData, 'JPEG', 0, 0);
    pdf.addPage();
  }
  pdf.save('download.pdf');
};
jspdf.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/1.3.2/jspdf.min.js';
document.body.appendChild(jspdf);
```

1. **Wait for the download**
   - The script will process each page and compile them into a PDF
   - Larger files may take several minutes to process
   - The downloaded file will be named "downloaded_file.pdf"

Source: Adapted from [GitHub - mhsohan/How-to-download-protected-view-only-files-from-google-drive](https://github.com/mhsohan/How-to-download-protected-view-only-files-from-google-drive-)
