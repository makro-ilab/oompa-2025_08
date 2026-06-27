from inspect import isclass

from makro_utils.log_manager import LogManager

logger = LogManager.get_logger("oompa.descriptors")


def descriptor_search[T](descriptors: list[T] | set[T], obj, inherit_class, descriptor_class: T):
    if not isclass(inherit_class):
        msg = f"{inherit_class} is not a class object"
        logger.error(msg)
        raise AttributeError(msg)
    if not isclass(descriptor_class):
        msg = f"{descriptor_class} is not a class object"
        logger.error(msg)
        raise AttributeError(msg)

    descriptor_name = str(descriptor_class)

    # TODO: could speed this up by caching descriptors in the relevant classes
    obj_cls = type(obj)
    if isclass(obj):
        obj_cls = obj
    mro_classes = obj_cls.mro()
    sv_meta_classes = [x for x in mro_classes if isinstance(x, inherit_class)]

    for cls in sv_meta_classes:
        for item in dir(cls):
            if item.startswith("_"):
                continue
            vars_cls = vars(cls)
            if item not in vars_cls:
                continue
            cls_obj = vars_cls[item]
            if isinstance(cls_obj, descriptor_class):
                logger.trace(f"  {item} is a {descriptor_name} Descriptor")
                if isinstance(descriptors, list):
                    descriptors.append(cls_obj)
                if isinstance(descriptors, set):
                    descriptors.add(cls_obj)
