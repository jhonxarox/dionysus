# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Appversion(models.Model):
    platform = models.TextField(db_column='Platform', blank=True, null=True)  # Field name made lowercase.
    app_version = models.TextField(db_column='App Version', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    date_release = models.TextField(db_column='Date Release', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.

    class Meta:
        managed = False
        db_table = 'appversion'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=80)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Fraud(models.Model):
    appsflyer_id = models.TextField(db_column='AppsFlyer ID', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.

    class Meta:
        managed = False
        db_table = 'fraud'


class Install(models.Model):
    id = models.BigAutoField(primary_key=True)
    attributed_touch_time = models.DateTimeField(db_column='Attributed Touch Time', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    install_time = models.DateTimeField(db_column='Install Time', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    media_source = models.TextField(db_column='Media Source', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    campaign = models.TextField(db_column='Campaign', blank=True, null=True)  # Field name made lowercase.
    campaign_id = models.TextField(db_column='Campaign ID', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    site_id = models.TextField(db_column='Site ID', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    appsflyer_id = models.TextField(db_column='AppsFlyer ID', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    platform = models.TextField(db_column='Platform', blank=True, null=True)  # Field name made lowercase.
    device_type = models.TextField(db_column='Device Type', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    app_version = models.TextField(db_column='App Version', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    is_retargeting = models.NullBooleanField(db_column='Is Retargeting')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    original_url = models.TextField(db_column='Original URL', blank=True, null=True)  # Field name made lowercase. Field renamed to remove unsuitable characters.
    ctit_status = models.NullBooleanField(db_column='CTIT Status')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    device_status = models.NullBooleanField(db_column='Device Status')  # Field name made lowercase. Field renamed to remove unsuitable characters.
    app_version_status = models.NullBooleanField(db_column='App Version Status')  # Field name made lowercase. Field renamed to remove unsuitable characters.

    class Meta:
        managed = False
        db_table = 'install'

    def __str__(self):
        return self.headline