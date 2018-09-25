from __future__ import absolute_import
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from django.forms.utils import ErrorList
from wagtail.wagtailcore import blocks

from ask_cfpb.models.django import Answer
from v1 import blocks as v1_blocks
from v1.atomic_elements import molecules


class AskMetadata(blocks.StructBlock):
    answer_id = blocks.IntegerBlock(
        required=True,
        label='Answer ID',
        help_text='ID for the Ask CFPB Answer you wish to pull in data from.'
    )

    def render(self, value, context=None):
        answer = Answer.objects.get(id=value['answer_id'])
        value['snippet'] = answer.snippet
        value['categories'] = answer.category.all()
        value['subcategories'] = answer.subcategory.all()
        value['related_questions'] = answer.related_questions.all()
        template = '_includes/organisms/ask-metadata.html'
        return render_to_string(template, value)


class AskHeadingLevelBlock(blocks.ChoiceBlock):
    choices = [
        ('h2', 'H2'),
        ('h3', 'H3'),
        ('h4', 'H4'),
        ('b', 'bold'),
    ]
    classname = 'heading-level-block'


class AskHeadingBlock(blocks.StructBlock):
    text = v1_blocks.HeadingTextBlock(required=False)
    level = v1_blocks.HeadingLevelBlock(default='h2')

    class Meta:
        classname = 'ask-heading-block'
        icon = 'title'
        template = '_includes/blocks/heading.html'
        form_template = (
            'admin/form_templates/struct-with-block-wrapper-classes.html'
        )


class NonAskLinkItem(blocks.StructBlock):
    link_text = blocks.CharBlock(required=True,)
    page_link = blocks.PageChooserBlock(
        required=False,
        help_text='Link to a page in Wagtail.',
        label='Page'
    )
    external_link = blocks.CharBlock(
        required=False,
        max_length=1000,
        label='Direct URL',
        help_text='Enter url for page outside Wagtail. This will only '
                  'be used if there is no page selected.'
    )

    def get_context(self, value, parent_context=None):
        return value

    class Meta:
        template = '_includes/ask/ask-link-item.html'


class AskLinkItem(blocks.StructBlock):
    answer_id = blocks.IntegerBlock(
        required=True,
        label='Answer ID',
        help_text='ID for the Ask CFPB Answer you wish to pull data from.'
    )
    link_text = blocks.CharBlock(
        label="Custom link text",
        required=False,
        help_text=('Override the default link text')
    )

    def get_context(self, value, parent_context=None):
        ctx = super(AskLinkItem, self).get_context(
            value, parent_context=parent_context)
        try:
            answer = Answer.objects.get(id=value['answer_id'])
            ctx['answer'] = answer
            if answer.english_page:
                ctx['page_link'] = answer.english_page
            ctx['link_text'] = value['link_text'] \
                if value['link_text'] else answer.statement
            return ctx
        except Exception:
            return

    def clean(self, value):
        cleaned = super(AskLinkItem, self).clean(value)

        if cleaned.get('answer_id'):
            try:
                answer = Answer.objects.get(id=cleaned['answer_id'])
            except ObjectDoesNotExist:
                raise ValidationError(
                    'Validation error in LinkItem: '
                    'Ask answer does not exist',
                    params={'answer_id': ErrorList([
                        'Answer with given id does not exist.'
                    ])}
                )

        return cleaned

    class Meta:
        template = '_includes/ask/ask-link-item.html'


class LinkColumn(blocks.StructBlock):
    heading = AskHeadingBlock(required=False, default={'level': 'h3'})
    links = blocks.StreamBlock(
        [
            ('ask_item', AskLinkItem()),
            ('link_item', NonAskLinkItem())
        ]
    )


class NonAskTextItem(blocks.StructBlock):
    heading = blocks.CharBlock(required=True)
    heading_level = AskHeadingLevelBlock(required=True, default='h4')
    body = blocks.TextBlock(required=True,
                            help_text=('Enter body text for this item.'))
    link_text = blocks.CharBlock(required=True,)
    page_link = blocks.PageChooserBlock(
        required=False,
        help_text='Link to a page in Wagtail.',
        label='Page'
    )
    external_link = blocks.CharBlock(
        required=False,
        max_length=1000,
        label='Direct URL',
        help_text='Enter url for page outside Wagtail. This will only '
                  'be used if there is no page selected.'
    )

    def get_context(self, value, parent_context=None):
        return value

    class Meta:
        template = '_includes/ask/ask-text-item.html'


class AskTextItem(blocks.StructBlock):
    answer_id = blocks.IntegerBlock(
        required=True,
        label='Answer ID',
        help_text='ID for the Ask CFPB Answer you wish to pull data from.'
    )
    heading = blocks.CharBlock(
        label="Custom heading text",
        required=False,
        help_text=('Override default heading text')
    )
    heading_level = AskHeadingLevelBlock(required=True, default='h4')
    body = blocks.TextBlock(
        required=True,
        help_text=('Enter body text for this item.'))
    link_text = blocks.CharBlock(
        required=True,)

    def get_context(self, value, parent_context=None):
        ctx = super(AskTextItem, self).get_context(
            value, parent_context=parent_context)
        try:
            answer = Answer.objects.get(id=value['answer_id'])
            ctx['answer'] = answer
            if answer.english_page:
                ctx['page_link'] = answer.english_page
            ctx['heading'] = value['heading'] \
                if value['heading'] else answer.statement
            ctx['body'] = value['body']
            ctx['link_text'] = value['link_text']
            ctx['heading_level'] = value['heading_level']
            return ctx
        except Exception:
                return

    def clean(self, value):
        cleaned = super(AskTextItem, self).clean(value)

        if cleaned.get('answer_id'):
            try:
                answer = Answer.objects.get(id=cleaned['answer_id'])
            except ObjectDoesNotExist:
                raise ValidationError(
                    'Validation error in TextItem: '
                    'Ask answer does not exist',
                    params={'answer_id': ErrorList([
                        'Answer with given id does not exist.'
                    ])}
                )

        return cleaned


    class Meta:
        template = '_includes/ask/ask-text-item.html'


class TextColumn(blocks.StructBlock):
    heading = AskHeadingBlock(
        required=False,
        default={'level': 'h3'})
    links = blocks.StreamBlock(
        [
            ('ask_item', AskTextItem()),
            ('text_item', NonAskTextItem()),
        ]
    )


class TextAndLinkBlock(blocks.StructBlock):
    heading = AskHeadingBlock(required=False,)
    intro = blocks.RichTextBlock(required=False)
    has_top_border = blocks.BooleanBlock(required=False)
    anchor_link = v1_blocks.AnchorLink()

    columns = blocks.StreamBlock(
        [
            ('ask_link_column', LinkColumn()),
            ('ask_text_column', TextColumn()),
            ('info_unit_column', molecules.InfoUnit())
        ]
    )

    class Meta:
        icon = 'title'
        template = '_includes/ask/ask-block.html'
