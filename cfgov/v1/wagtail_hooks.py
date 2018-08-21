import logging

from django.conf import settings
from django.conf.urls import url
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.html import format_html_join

from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from wagtail.wagtailadmin.menu import MenuItem
from wagtail.wagtailcore import hooks

from v1.admin_views import manage_cdn
from v1.models.menu_item import MenuItem as MegaMenuItem
from v1.util import util


logger = logging.getLogger(__name__)


@hooks.register('before_delete_page')
def raise_delete_error(request, page):
    raise PermissionDenied('Deletion via POST is disabled')


@hooks.register('after_delete_page')
def log_page_deletion(request, page):
    logger.warning(
        (
            u'User {user} with ID {user_id} deleted page {title} '
            u'with ID {page_id} at URL {url}'
        ).format(
            user=request.user,
            user_id=request.user.id,
            title=page.title,
            page_id=page.id,
            url=page.url_path,
        )
    )


def check_permissions(parent, user, is_publishing, is_sharing):
    parent_perms = parent.permissions_for_user(user)
    if parent.slug != 'root':
        is_publishing = is_publishing and parent_perms.can_publish()


@hooks.register('insert_editor_js')
def editor_js():
    js_files = [
        'js/table-block.js',
    ]
    js_includes = format_html_join(
        '\n',
        '<script src="{0}{1}"></script>',
        ((settings.STATIC_URL, filename) for filename in js_files)
    )

    return js_includes


@hooks.register('insert_editor_css')
def editor_css():
    css_files = [
        'css/bureau-structure.css',
        'css/deprecated-blocks.css',
        'css/general-enhancements.css',
        'css/heading-block.css',
        'css/info-unit-group.css',
        'css/table-block.css',
    ]
    css_includes = format_html_join(
        '\n',
        '<link rel="stylesheet" href="{0}{1}">',
        ((settings.STATIC_URL, filename) for filename in css_files)
    )

    return css_includes


@hooks.register('cfgovpage_context_handlers')
def form_module_handlers(page, request, context, *args, **kwargs):
    """
    Hook function that iterates over every Streamfield's blocks on a page and
    sets the context for any form modules.
    """
    form_modules = {}
    streamfields = util.get_streamfields(page)

    for fieldname, blocks in streamfields.items():
        for index, child in enumerate(blocks):
            if hasattr(child.block, 'get_result'):
                if fieldname not in form_modules:
                    form_modules[fieldname] = {}

                if not request.method == 'POST':
                    is_submitted = child.block.is_submitted(
                        request,
                        fieldname,
                        index
                    )
                    module_context = child.block.get_result(
                        page,
                        request,
                        child.value,
                        is_submitted
                    )
                    form_modules[fieldname].update({index: module_context})
    if form_modules:
        context['form_modules'] = form_modules


@hooks.register('register_admin_menu_item')
def register_django_admin_menu_item():
    return MenuItem(
        'Django Admin',
        reverse('admin:index'),
        classnames='icon icon-redirect',
        order=99999
    )


@hooks.register('register_admin_menu_item')
def register_frank_menu_item():
    return MenuItem('CDN Tools',
                    reverse('manage-cdn'),
                    classnames='icon icon-cogs',
                    order=10000)


@hooks.register('register_admin_urls')
def register_flag_admin_urls():
    return [url(r'^cdn/$', manage_cdn, name='manage-cdn'), ]


@hooks.register('before_serve_page')
def serve_latest_draft_page(page, request, args, kwargs):
    if page.pk in settings.SERVE_LATEST_DRAFT_PAGES:
        latest_draft = page.get_latest_revision_as_page()
        response = latest_draft.serve(request, *args, **kwargs)
        response['Serving-Wagtail-Draft'] = '1'
        return response


@hooks.register('before_serve_shared_page')
def before_serve_shared_page(page, request, args, kwargs):
    request.show_draft_megamenu = True


class MegaMenuModelAdmin(ModelAdmin):
    model = MegaMenuItem
    menu_label = 'Mega Menu'
    menu_icon = 'cog'
    list_display = ('link_text', 'order')


modeladmin_register(MegaMenuModelAdmin)


@receiver(post_save, sender=MegaMenuItem)
def clear_mega_menu_cache(sender, instance, **kwargs):
    from django.core.cache import caches
    caches['default_fragment_cache'].delete('mega_menu')
