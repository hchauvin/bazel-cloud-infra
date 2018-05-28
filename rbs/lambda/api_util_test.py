# Copyright 2018 The Bazel Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import api_util


class ApiUtilTest(unittest.TestCase):

  def test_get_positive_int(self):
    self.assertEqual(api_util.Params({"foo": "10"}).get_positive_int("foo"), 10)
    self.assertRaises(api_util.InvalidArgumentException,
                      api_util.Params({
                          "foo": "10"
                      }).get_positive_int, "bar")
    self.assertRaises(api_util.InvalidArgumentException,
                      api_util.Params({
                          "foo": "-10"
                      }).get_positive_int, "foo")
    self.assertRaises(api_util.InvalidArgumentException,
                      api_util.Params({
                          "foo": "10abc"
                      }).get_positive_int, "foo")

  def test_get_one_of(self):
    options = ["Bar"]
    self.assertEqual(
        api_util.Params({
            "foo": "Bar"
        }).get_one_of("foo", options), "Bar")
    self.assertRaises(api_util.InvalidArgumentException,
                      api_util.Params({
                          "foo": "Qux"
                      }).get_one_of, "foo", options)
    self.assertRaises(api_util.InvalidArgumentException,
                      api_util.Params({}).get_one_of, "foo", options)

  def test_get_bool(self):
    self.assertEqual(api_util.Params({"foo": "true"}).get_bool("foo"), True)
    self.assertEqual(api_util.Params({}).get_bool("foo"), False)


if __name__ == '__main__':
  unittest.main()
