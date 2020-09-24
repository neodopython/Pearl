'''
MIT License

Copyright (c) 2020 Caio Alexandre

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import discord


class Embed(discord.Embed):
    """A custom ``Embed`` constructor. In this constructor we don't need to call ``Embed``'s methods."""
    def __init__(self, **kwargs):
        options = {
            'fields': {
                'type': list,
                'function': lambda args: list(map(lambda arg: self.add_field(**arg), args))
            },
            'footer': {
                'type': dict,
                'function': lambda args: self.set_footer(**args)
            },
            'author': {
                'type': dict,
                'function': lambda args: self.set_author(**args)
            },
            'image': {
                'type': str,
                'function': lambda url: self.set_image(url=url)
            },
            'thumbnail': {
                'type': str,
                'function': lambda url: self.set_thumbnail(url=url)
            }
        }

        for option in options:
            embed_attr = kwargs.get(option)
            option_attr = options.get(option)

            if not embed_attr:
                continue

            if not isinstance(embed_attr, option_attr['type']):
                option_type = option_attr['type'].__name__
                embed_type = type(embed_attr).__name__

                raise TypeError(f'{option} type must be {option_type}, not {embed_type}')

            option_attr['function'](embed_attr)
            
        del options
        super().__init__(**kwargs)