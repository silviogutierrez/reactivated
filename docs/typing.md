---
id: typing
title: Typing
sidebar_label: Typing
---

We need a way to easily specify fields available per model to the template layer.
We can't just pass the entire model because this is unsafe and has performance
issues.

## Option 1
Completely manual.

```python
class PostData(NamedTuple):
    name: str
    url: str


class PostDetailProps(NamedTuple):
    post: PostData
    another_prop: str
```

You then have to manually build PostData, like so:

```python
p = models.Post.objects.first()

PostDetailProps(
    another_prop='something',
    post=PostData(
        name=post.name,
        url=post.url,
    ),
)
```

## Option 2
A true generic class. This feels the cleanest, overall. Less verbose than manual
typing, but still not that compact.

```python
from reactivated import Data

class PostData(Data[models.Post]):
    fields = [
        'name',
        'url',
    ]

class PostDetailProps(NamedTuple):
    post: PostData
    another_prop: str
```

Usage would then be simpler:

```python
p = models.Post.objects.first()

PostDetailProps(
    another_prop='something',
    post=PostData(p),
)
```

## Option 3
Simply use the post model as the typing, and have the `ssr` decorator make sure
you also define serialization logic.


```python
class PostDetailProps(NamedTuple):
    post: models.Post
    another_prop: str

    class Serialization:
        post = [
            'name',
            'url',
        ]

```

Or for better typing, maybe something like:

```python
from reactivated import Serialization

class PostDetailProps(NamedTuple):
    post: models.Post
    another_prop: str

    serialization = Serialization(
        post=[
            'name',
            'url',
        ],
    )
```

If you forget to specify serialization logic, we do a runtime "compiler" check
and mention what is needed.


## Considerations

1. List views and detail views likely use the same serialization logic, though
   list views may be sparser. What's the best way to reuse this?

2. If we go with a data-only object, what's the best name for this? PostRecord?
   PostData? Etc?

   Likes:

   * Record

   Dislikes:

   * Data
   * Structure
   * Object
