"""探针统一语言引脚（R52）。

为什么要 pin：R52 起站点按浏览器语言自动判定界面语言（判定链
`__i18nPin > ?lang= > localStorage.nikki_lang > navigator.languages > zh`），
而 Playwright 的 Chromium 默认 `navigator.languages` 是 en-US，会让
r37/r38/r39/r41/r42/r43/r45 这些以中文文案为基线的断言成片失配。

`window.__i18nPin` 优先级最高，且在 `add_init_script` 里注入的脚本先于页面
任何脚本执行（file:// 下同样成立），因此本模块只做一件事：把 pin 写进 context。

用法：
    from i18n_pin import pin
    ctx = pin(browser.new_context(viewport={...}))
    page = ctx.new_page()

注意：必须在 `new_page()` / 首次 `goto()` 之前调用；对同一 context 的
所有导航与 reload 都生效。
"""

from __future__ import annotations

PIN_JS = "try{window.__i18nPin='%s'}catch(e){}"


def pin(ctx, lang: str = "zh"):
    """把语言 pin 挂到 Playwright context 上，返回同一个 ctx 便于链式书写。"""
    if lang not in ("zh", "en", "fr", "es", "ru", "ar"):
        raise ValueError("unsupported lang: %r" % (lang,))
    ctx.add_init_script(PIN_JS % lang)
    return ctx


class _PinnedBrowser:
    """把 browser.new_context() 包一层，自动 pin —— 探针里常见 new_context(...).new_page() 链式写法，
    逐个改链太脆，包 browser 一次即可覆盖全部 context。"""

    def __init__(self, browser, lang="zh"):
        self._browser = browser
        self._lang = lang

    def new_context(self, *a, **kw):
        return pin(self._browser.new_context(*a, **kw), self._lang)

    def __getattr__(self, name):
        return getattr(self._browser, name)


def pin_browser(browser, lang: str = "zh"):
    return _PinnedBrowser(browser, lang)
