from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="sa_hr_onboarding",
    version="0.0.1",
    description="Saudi HR Auto-Onboarding for Frappe HRMS",
    author="IRSAA Business Solution",
    author_email="hr@irsaa.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
