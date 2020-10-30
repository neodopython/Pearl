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

from discord.ext.commands import CommandError


class MusicException(CommandError):
    """Generic exception for music commands errors."""


class RequesterNotConnected(MusicException):
    def __init__(self):
        super().__init__('Join a voicechannel first')


class BotNotConnected(MusicException):
    def __init__(self):
        super().__init__('Not connected')


class CannotConnect(MusicException):
    def __init__(self):
        super().__init__('Connect and Speak permissions is needed')


class WrongChannel(MusicException):
    def __init__(self):
        super().__init__('You need to be in my voicechannel')


class NothingFound(MusicException):
    def __init__(self):
        super().__init__('No tracks found')


class AlreadyPaused(MusicException):
    def __init__(self):
        super().__init__('Player already paused')


class AlreadyResumed(MusicException):
    def __init__(self):
        super().__init__('Player already resumed')


class InvalidSeekTime(MusicException):
    def __init__(self):
        super().__init__('Invalid seek time')


class InvalidVolume(MusicException):
    def __init__(self):
        super().__init__('Invalid volume')


class NotDJ(MusicException):
    def __init__(self):
        super().__init__('You are not DJ or an administrador')


class CannotRemoveMusic(MusicException):
    def __init__(self):
        super().__init__('Cannot remove this song from queue')


class NothingInQueue(MusicException):
    def __init__(self):
        super().__init__('Nothing in queue')


class AlreadyVoted(MusicException):
    def __init__(self):
        super().__init__('Already voted to skip this music')


class InvalidValueIndex(MusicException):
    def __init__(self):
        super().__init__('Invalid value index')


class InvalidMusicIndex(MusicException):
    def __init__(self):
        super().__init__('Invalid music index')


class BotNotPlaying(MusicException):
    def __init__(self):
        super().__init__('Nothing playing')


# TODO: Add docstring for this class.
class ResponseError(CommandError):
    def __init__(self):
        super().__init__('Not OK response')