OBS_PROJECT := EA4-experimental
OBS_PACKAGE := ea-memcached
DISABLE_BUILD := repository=CentOS_9 repository=Almalinux_10
include $(EATOOLS_BUILD_DIR)obs.mk
