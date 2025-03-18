from django.contrib.auth.models import User
from django.db.models import CharField,RESTRICT,OneToOneField,ForeignKey,Model,SET_NULL,IntegerField,RESTRICT
from django.core.validators import MinValueValidator, RegexValidator

ColorRegex = RegexValidator(r"^#[a-fA-F0-9]{6}$", message="Invalid Hex color")


class University(Model):
    name = CharField(max_length=200,null=False,blank=False,verbose_name='University Name')
    
    class Meta:
        verbose_name = "University"
        verbose_name_plural = "Universities"
        
    def __str__(self):
        return self.name

class Institute(Model):
    name = CharField(max_length=200,null=False,blank=False,verbose_name='Institute Name')
    university = ForeignKey(to=University,null=False,blank=False,related_name='insti',on_delete=RESTRICT)
    location = CharField(max_length=200,null=False,blank=False,verbose_name='Location')
    
    class Meta:
        verbose_name = "Institute"
        verbose_name_plural = "Institutes"
    
    def __str__(self):
        return f"{self.university}:{self.name}"
    
class Branch(Model):
    name = CharField(max_length=200,null=False,blank=False,verbose_name='Branch Name')
    institute = ForeignKey(to=Institute,null=False,on_delete=RESTRICT,related_name='branch')

    class Meta:
        verbose_name = "Branch"
        verbose_name_plural = "Branches"

    def __str__(self):
        return f"{self.institute}:{self.name}"

class Subjects(Model):
    name = CharField(max_length=200,null=False,blank=False,verbose_name='Subject Name')
    semester = IntegerField(verbose_name='Semester',validators=[MinValueValidator(1)])
    branch = ForeignKey(to=Branch,null=True,blank=False,on_delete=RESTRICT,related_name='subject')
    
    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
    
    
    def __str__(self):
        return f"{self.name} - {self.semester} - {self.branch}"

class Color(Model):
    institute = OneToOneField(to=Institute,null=True,blank=False,related_name='color',on_delete=RESTRICT)
    main_color = CharField(max_length=7,null=False,blank=False,verbose_name="Main Color",validators=[ColorRegex])
    sec_color = CharField(max_length=7,null=False,blank=False,verbose_name="Secondary Color",validators=[ColorRegex])
    
    class Meta:
        verbose_name = "Color Theme"
        verbose_name_plural = "Color Themes"
        
    def __str__(self):
        return  f"Color Theme: {self.institute.name}" #f"Main Theme: {self.main_color}, Secondary Theme: {self.sec_color}"