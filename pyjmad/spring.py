import jpype

org = jpype.JPackage('org')
AnnotationConfigApplicationContext = org.springframework.context.annotation.AnnotationConfigApplicationContext
ClassPathXmlApplicationContext = org.springframework.context.support.ClassPathXmlApplicationContext

class SpringApplicationContext(object):
    def __init__(self, configuration):
        if type(configuration) is str:
            self._context = ClassPathXmlApplicationContext(configuration)
        else:
            self._context = AnnotationConfigApplicationContext(configuration)

    def bean_definitions(self):
        return [str(s) for s in self._context.getBeanDefinitionNames()]

    def __getitem__(self, bean):
        return self._context.getBean(bean)

    def __setitem__(self, k, v):
        raise NotImplementedError('Setting of Beans is not supported')

    def __delitem__(self, k):
        raise NotImplementedError('Deletion of Beans is not supported')

    def __iter__(self):
        for s in self.bean_definitions():
            yield self.__getitem__(s)

    def __len__(self):
        return len(self.bean_definitions())

    def __repr__(self):
        return str(self._context.toString())

    def __str__(self):
        return str(self._context.toString())

    def _ipython_key_completions_(self):
        return self.bean_definitions()
