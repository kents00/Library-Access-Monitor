# Flash Messages - Standard Setup

This is a standard setup for handling flash messages in Flask applications using Notiflix.

## Implementation Steps

1. **Include required files**:
   - Copy `flash-messages.js` to your project's static/js folder
   - Copy `_flash_messages.html` to your project's templates folder

2. **Include in base template**:
   Add this line before the closing `</body>` tag in your base template:
   ```html
   {% include '_flash_messages.html' %}
   ```

3. **Use in Flask routes**:
   ```python
   flash('Your message', 'success')  # Categories: success, error, warning, info
   ```

4. **Pass backend errors**:
   ```python
   return render_template('template.html', error='Error message')
   ```

5. **Form loading indicators**:
   Forms will automatically show a loading indicator unless you add the
   `data-no-loading` attribute to the form tag.

6. **Manual notifications**:
   You can also manually trigger notifications in JavaScript:
   ```javascript
   showNotification('success', 'Operation completed successfully!');
   showLoading('Processing your request...');
   hideLoading();
   ```

This setup provides a consistent way to display notifications across your application.
