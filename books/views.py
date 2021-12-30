import inspect
import functools

from django.shortcuts import render
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy

# from django.utils.decorators import method_decorator

from .forms import AuthorForm, BookForm
from .models import Author, Book


# def inspect_cbv(func):
#     def decorator__init(self, *args, **kwargs):
#         print("Decorator running")
#         # print(args, kwargs)
#         # return func(*args, **kwargs)

#     func.__init__ = decorator__init
#     return decorator__init


def time_this(func):
    def wrapped(*args, **kwargs):
        print("_________timer starts_________")
        from datetime import datetime

        before = datetime.now()
        x = func(*args, **kwargs)
        after = datetime.now()
        print("** elapsed Time = {0} **\n".format(after - before))
        return x

    return wrapped


def time_all_class_methods(Cls):
    # decoration body - doing nothing really since we need to wait until the decorated object is instantiated
    class Wrapper:
        def __init__(self, *args, **kwargs):
            print(f"__init__() called with args: {args} and kwargs: {kwargs}")
            self.decorated_obj = Cls(*args, **kwargs)

        def __getattribute__(self, s):
            try:
                x = super().__getattribute__(s)
                return x
            except AttributeError:
                pass
            x = self.decorated_obj.__getattribute__(s)
            if type(x) == type(self.__init__):  # it is an instance method
                print(f"attribute belonging to decorated_obj: {x.__qualname__}")
                return time_this(
                    x
                )  # this is equivalent of just decorating the method with time_this
            else:
                return x

    return Wrapper  # decoration ends here


INSPECT_LOGS = {}


class FunctionLog:
    def __init__(self):
        self.tab_index = 0
        self.ordering = 0
        self.args = ()
        self.kwargs = {}
        self.name = None
        self.ret_value = None


class InspectorMixin:
    tab_index = 0
    func_order = 0

    @property
    def get_whitelisted_callables(self):
        cbv_funcs = list(
            filter(
                lambda x: not x[0].startswith("__"),
                inspect.getmembers(self.__class__, inspect.isfunction),
            )
        )
        return [func[0] for func in cbv_funcs]

    def __getattribute__(self, name: str):
        attr = super().__getattribute__(name)

        if (
            callable(attr)
            and name != "__class__"
            and attr.__name__ in self.get_whitelisted_callables
        ):
            tab = "\t"
            f = FunctionLog()

            @functools.wraps(attr)
            def wrapper(*args, **kwargs):
                print(f"{tab*self.tab_index} QUALNAME --> {attr.__qualname__}")
                print(
                    f"{tab*self.tab_index} Before calling {attr.__qualname__} with args {args} and kwargs {kwargs}"
                )
                # print(inspect.getsource(attr))
                # print(inspect.getframeinfo(inspect.currentframe()).function)
                self.tab_index += 1
                self.func_order += 1
                f.ordering = self.func_order

                print(f"{tab*self.tab_index} FUNC ORDER --> ", self.func_order)

                res = attr(*args, **kwargs)
                print(
                    f"{tab*self.tab_index} Result of {attr.__qualname__} call is {res}"
                )

                # Update function log
                f.name = attr.__qualname__
                f.tab_index = self.tab_index
                f.args = args
                f.kwargs = kwargs
                f.ret_value = res

                global INSPECT_LOGS
                INSPECT_LOGS[f.ordering] = f

                self.tab_index -= 1
                print(f"{tab*self.tab_index} After calling {attr.__qualname__}\n")
                return res

            return wrapper
        return attr


# ListView.__getattribute__ = InspectorMixin.__getattribute__
# for cls in ListView.mro():
#     if cls.__name__ != "object":
#         cls.__getattribute__ = InspectorMixin.__getattribute__


class BookListView(InspectorMixin, ListView):
    model = Book

    def get_favorite_book(self):
        return "Harry Potter"

    def get_context_data(self, **kwargs):
        x = 1
        context = super(BookListView, self).get_context_data(**kwargs)
        context["now"] = "the time right now"
        fav_book = self.get_favorite_book()
        context["fav_book"] = fav_book
        return context


class BookDetailView(DetailView):
    model = Book


class BookCreateView(CreateView):
    model = Book
    form_class = BookForm


class BookUpdateView(UpdateView):
    model = Book
    form_class = BookForm

    def get_success_url(self) -> str:
        return reverse_lazy("book_detail", kwargs={"pk": self.object.pk})


class BookDeleteView(DeleteView):
    model = Book
    success_url = reverse_lazy("books")


class AuthorCreateView(CreateView):
    model = Author
    form_class = AuthorForm
    success_url = reverse_lazy("books")
