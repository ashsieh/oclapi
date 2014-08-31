from django.core.validators import RegexValidator
from rest_framework import serializers
from concepts.models import ConceptReference
from oclapi.fields import HyperlinkedResourceVersionIdentityField
from oclapi.models import NAMESPACE_REGEX
from oclapi.serializers import ResourceVersionSerializer
from settings import DEFAULT_LOCALE
from collection.models import Collection, CollectionVersion
from oclapi.models import ACCESS_TYPE_CHOICES, DEFAULT_ACCESS_TYPE


class CollectionListSerializer(serializers.Serializer):
    id = serializers.CharField(required=True, source='mnemonic')
    name = serializers.CharField(required=True)
    url = serializers.CharField()
    owner = serializers.CharField(source='parent_resource')
    owner_type = serializers.CharField(source='parent_resource_type')
    owner_url = serializers.CharField(source='parent_url')

    class Meta:
        model = Collection


class CollectionCreateOrUpdateSerializer(serializers.Serializer):
    class ActiveConceptsField(serializers.IntegerField):
        def field_to_native(self, obj, field_name):
            return ConceptReference.objects.filter(is_active=True, parent_id=obj.id).count()

    class Meta:
        model = Collection
        lookup_field = 'mnemonic'

    def restore_object(self, attrs, instance=None):
        collection = instance if instance else Collection()
        collection.mnemonic = attrs.get(self.Meta.lookup_field, collection.mnemonic)
        collection.name = attrs.get('name', collection.name)
        collection.full_name = attrs.get('full_name', collection.full_name)
        collection.description = attrs.get('description', collection.description)
        collection.collection_type = attrs.get('collection_type', collection.collection_type)
        collection.public_access = attrs.get('public_access', collection.public_access or DEFAULT_ACCESS_TYPE)
        collection.default_locale=attrs.get('default_locale', collection.default_locale or DEFAULT_LOCALE)
        collection.website = attrs.get('website', collection.website)
        collection.supported_locales = attrs.get('supported_locales').split(',') if attrs.get('supported_locales') else collection.supported_locales
        collection.extras = attrs.get('extras', collection.extras)
        return collection


class CollectionCreateSerializer(CollectionCreateOrUpdateSerializer):
    type = serializers.CharField(source='resource_type', read_only=True)
    uuid = serializers.CharField(source='id', read_only=True)
    id = serializers.CharField(required=True, validators=[RegexValidator(regex=NAMESPACE_REGEX)], source='mnemonic')
    short_code = serializers.CharField(source='mnemonic', read_only=True)
    name = serializers.CharField(required=True)
    full_name = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    collection_type = serializers.CharField(required=False)
    public_access = serializers.ChoiceField(required=False, choices=ACCESS_TYPE_CHOICES)
    default_locale = serializers.CharField(required=False)
    supported_locales = serializers.CharField(required=False)
    website = serializers.CharField(required=False)
    url = serializers.CharField(read_only=True)
    versions_url = serializers.CharField(read_only=True)
    concepts_url = serializers.CharField(read_only=True)
    active_concepts = CollectionCreateOrUpdateSerializer.ActiveConceptsField(read_only=True)
    owner = serializers.CharField(source='parent_resource', read_only=True)
    owner_type = serializers.CharField(source='parent_resource_type', read_only=True)
    owner_url = serializers.CharField(source='parent_url', read_only=True)
    versions = serializers.IntegerField(source='num_versions', read_only=True)
    created_on = serializers.DateTimeField(source='created_at', read_only=True)
    updated_on = serializers.DateTimeField(source='updated_at', read_only=True)
    created_by = serializers.CharField(source='owner', read_only=True)
    updated_by = serializers.CharField(read_only=True)
    extras = serializers.WritableField(required=False)

    def save_object(self, obj, **kwargs):
        errors = Collection.persist_new(obj, **kwargs)
        self._errors.update(errors)


class CollectionDetailSerializer(CollectionCreateOrUpdateSerializer):
    type = serializers.CharField(source='resource_type', read_only=True)
    uuid = serializers.CharField(source='id', read_only=True)
    id = serializers.CharField(required=False, validators=[RegexValidator(regex=NAMESPACE_REGEX)], source='mnemonic')
    short_code = serializers.CharField(source='mnemonic', read_only=True)
    name = serializers.CharField(required=False)
    full_name = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    collection_type = serializers.CharField(required=False)
    public_access = serializers.ChoiceField(required=False, choices=ACCESS_TYPE_CHOICES)
    default_locale = serializers.CharField(required=False)
    supported_locales = serializers.CharField(required=False)
    website = serializers.CharField(required=False)
    url = serializers.CharField(read_only=True)
    versions_url = serializers.CharField(read_only=True)
    concepts_url = serializers.CharField(read_only=True)
    active_concepts = CollectionCreateOrUpdateSerializer.ActiveConceptsField(read_only=True)
    owner = serializers.CharField(source='parent_resource', read_only=True)
    owner_type = serializers.CharField(source='parent_resource_type', read_only=True)
    owner_url = serializers.CharField(source='parent_url', read_only=True)
    versions = serializers.IntegerField(source='num_versions', read_only=True)
    created_on = serializers.DateTimeField(source='created_at', read_only=True)
    updated_on = serializers.DateTimeField(source='updated_at', read_only=True)
    created_by = serializers.CharField(source='owner', read_only=True)
    updated_by = serializers.CharField(read_only=True)
    extras = serializers.WritableField(required=False)

    def save_object(self, obj, **kwargs):
        request_user = self.context['request'].user
        errors = Collection.persist_changes(obj, request_user, **kwargs)
        self._errors.update(errors)


class CollectionVersionListSerializer(ResourceVersionSerializer):
    id = serializers.CharField(source='mnemonic')
    released = serializers.CharField()
    owner = serializers.CharField(source='parent_resource')
    owner_type = serializers.CharField(source='parent_resource_type')
    owner_url = serializers.CharField(source='parent_url')

    class Meta:
        model = CollectionVersion
        versioned_object_view_name = 'collection-detail'
        versioned_object_field_name = 'url'


class CollectionVersionDetailSerializer(ResourceVersionSerializer):
    type = serializers.CharField(required=True, source='resource_type')
    id = serializers.CharField(required=True, source='mnemonic')
    description = serializers.CharField()
    released = serializers.BooleanField()
    owner = serializers.CharField(source='parent_resource')
    owner_type = serializers.CharField(source='parent_resource_type')
    owner_url = serializers.CharField(source='parent_url')
    created_on = serializers.DateTimeField(source='created_at')
    updated_on = serializers.DateTimeField(source='updated_at')
    extras = serializers.WritableField()

    class Meta:
        model = CollectionVersion
        versioned_object_view_name = 'collection-detail'
        versioned_object_field_name = 'collectionUrl'

    def get_default_fields(self):
        default_fields = super(CollectionVersionDetailSerializer, self).get_default_fields()
        if self.opts.view_name is None:
            self.opts.view_name = self._get_default_view_name(self.opts.model)
        default_fields.update(
            {
                'parentVersionUrl': HyperlinkedResourceVersionIdentityField(related_attr='parent_version', view_name=self.opts.view_name),
                'previousVersionUrl': HyperlinkedResourceVersionIdentityField(related_attr='previous_version', view_name=self.opts.view_name),
            }
        )
        return default_fields


class CollectionVersionCreateOrUpdateSerializer(serializers.Serializer):
    class Meta:
        model = CollectionVersion
        lookup_field = 'mnemonic'

    def restore_object(self, attrs, instance=None):
        instance.mnemonic = attrs.get(self.Meta.lookup_field, instance.mnemonic)
        instance.description = attrs.get('description', instance.description)
        was_released = instance.released
        instance.released = attrs.get('released', instance.released)
        if was_released and not instance.released:
            self._errors['released'] = ['Cannot set this field to "false".  (Releasing another version will cause this field to become false.)']
        instance._was_released = was_released
        instance._previous_version_mnemonic = attrs.get('previous_version_mnemonic', instance.previous_version_mnemonic)
        instance._parent_version_mnemonic = attrs.get('parent_version_mnemonic', instance.parent_version_mnemonic)
        instance.extras = attrs.get('extras', instance.extras)
        return instance

    def save_object(self, obj, **kwargs):
        errors = CollectionVersion.persist_changes(obj, **kwargs)
        self._errors.update(errors)


class CollectionVersionUpdateSerializer(CollectionVersionCreateOrUpdateSerializer):
    id = serializers.CharField(required=False, source='mnemonic')
    released = serializers.BooleanField(required=False)
    description = serializers.CharField(required=False)
    previous_version = serializers.CharField(required=False, source='previous_version_mnemonic')
    parent_version = serializers.CharField(required=False, source='parent_version_mnemonic')
    extras = serializers.WritableField(required=False)


class CollectionVersionCreateSerializer(CollectionVersionCreateOrUpdateSerializer):
    id = serializers.CharField(required=True, validators=[RegexValidator(regex=NAMESPACE_REGEX)], source='mnemonic')
    released = serializers.BooleanField(required=False)
    description = serializers.CharField(required=False)
    previous_version = serializers.CharField(required=False, source='previous_version_mnemonic')
    parent_version = serializers.CharField(required=False, source='parent_version_mnemonic')
    extras = serializers.WritableField(required=False)

    def restore_object(self, attrs, instance=None):
        version = CollectionVersion()
        version.mnemonic = attrs.get(self.Meta.lookup_field)
        return super(CollectionVersionCreateSerializer, self).restore_object(attrs, instance=version)

    def save_object(self, obj, **kwargs):
        errors = CollectionVersion.persist_new(obj, **kwargs)
        self._errors.update(errors)
