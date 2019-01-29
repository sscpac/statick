import os

from statick_tool.args import Args


def test_args_init():
    # Expected result: parser and pre_parser are initialized
    args = Args('test')
    assert(args.pre_parser)
    assert(args.parser)


def test_args_user_paths_missing():
    # Expected result: No paths
    args = Args('test')
    user_paths = args.get_user_paths([])
    assert(user_paths == [])


def test_args_user_paths_undefined():
    # Expected result: No paths
    args = Args('test')
    user_paths = args.get_user_paths(['--user-paths', None])
    assert(user_paths == [])


def test_args_user_paths_multiple_definitions():
    # expected result: The second entry wins
    args = Args('test')
    user_paths = args.get_user_paths(['--user-paths',
                                      os.path.join(os.path.dirname(__file__),
                                                   'test'),
                                      '--user-paths',
                                      os.path.join(os.path.dirname(__file__),
                                                   'test2')])
    # Expected result: only the second is used
    assert(user_paths == [os.path.join(os.path.dirname(__file__), 'test2')])


def test_args_user_paths_multiple_paths():
    args = Args('test')
    user_paths = args.get_user_paths(['--user-paths',
                                      os.path.join(os.path.dirname(__file__),
                                                   'test') + ',' +
                                      os.path.join(os.path.dirname(__file__),
                                                   'test2')])
    # Expected result: both show up
    assert(user_paths == [os.path.join(os.path.dirname(__file__), 'test'),
                          os.path.join(os.path.dirname(__file__), 'test2')])


def test_args_user_paths_missing_dir():
    # expected result: no paths
    args = Args('test')
    user_paths = args.get_user_paths(['--user-paths', 'nonexistent'])
    assert(user_paths == [])


def test_args_user_paths_present():
    # expected result: The path we specified
    args = Args('test')
    user_paths = args.get_user_paths(['--user-paths',
                                     os.path.join(os.path.dirname(__file__),
                                                  'test')])
    assert(user_paths == [os.path.join(os.path.dirname(__file__), 'test')])
