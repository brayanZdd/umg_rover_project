from django import forms

class RegistroForm(forms.Form):
    nombre = forms.CharField(max_length=100)
    correo = forms.EmailField(max_length=100)
    confirmar_correo = forms.EmailField(max_length=100)
    telefono = forms.CharField(max_length=100)
    confirmar_telefono = forms.CharField(max_length=100)
    nickname = forms.CharField(max_length=45)
    password = forms.CharField(widget=forms.PasswordInput)
    confirmar_password = forms.CharField(widget=forms.PasswordInput)
    # NO hay campo avatar aquí
    
    def clean(self):
        cleaned_data = super().clean()
        correo = cleaned_data.get('correo')
        confirmar_correo = cleaned_data.get('confirmar_correo')
        telefono = cleaned_data.get('telefono')
        confirmar_telefono = cleaned_data.get('confirmar_telefono')
        password = cleaned_data.get('password')
        confirmar_password = cleaned_data.get('confirmar_password')
        
        if correo and confirmar_correo and correo != confirmar_correo:
            self.add_error('confirmar_correo', 'Los correos no coinciden')
        
        if telefono and confirmar_telefono and telefono != confirmar_telefono:
            self.add_error('confirmar_telefono', 'Los teléfonos no coinciden')
        
        if password and confirmar_password and password != confirmar_password:
            self.add_error('confirmar_password', 'Las contraseñas no coinciden')
        
        return cleaned_data

class LoginForm(forms.Form):
    nickname = forms.CharField(max_length=45)
    password = forms.CharField(widget=forms.PasswordInput)