from setuptools import setup
from setuptools.command.install import install
import sys

class PostInstallCommand(install):
    """Проверка Firebird client после установки пакета."""
    def run(self):
        install.run(self)
        try:
            import firebird.driver as fb

            if sys.platform == "darwin":
                fb.register_client_library("/opt/homebrew/lib/libfbclient.dylib")
            elif sys.platform.startswith("linux"):
                fb.register_client_library("/usr/lib/x86_64-linux-gnu/libfbclient.so")

            print("✅ Firebird client library доступна.")
        except Exception:
            print("\n⚠️ Firebird client library не найдена!")
            if sys.platform == "darwin":
                print("Установите через Homebrew: brew install firebird")
            elif sys.platform.startswith("linux"):
                print("Установите через пакетный менеджер, например: sudo apt install firebird-dev")
            else:
                print("Скачайте клиент с https://firebirdsql.org/en/server-packages/")
            print("После установки убедитесь, что библиотека доступна для Python.\n")

setup(
    name="autodealer",
    version="0.0.1",
    packages=["autodealer"],
    install_requires=[
        "firebird-driver>=1.0.0",
    ],
    python_requires=">=3.8",
    cmdclass={
        'install': PostInstallCommand,
    },
)
