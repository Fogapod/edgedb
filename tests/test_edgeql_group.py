##
# Copyright (c) 2012-present MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import os.path
import unittest

from edgedb.server import _testbase as tb


class TestEdgeQLGroup(tb.QueryTestCase):
    SCHEMA = os.path.join(os.path.dirname(__file__), 'schemas',
                          'queries.eschema')

    SCHEMA_TESTLP = os.path.join(os.path.dirname(__file__), 'schemas',
                                 'linkprops.eschema')

    SETUP = r"""
        #
        # MODULE test
        #

        WITH MODULE test
        INSERT Priority {
            name := 'High'
        };

        WITH MODULE test
        INSERT Priority {
            name := 'Low'
        };

        WITH MODULE test
        INSERT Status {
            name := 'Open'
        };

        WITH MODULE test
        INSERT Status {
            name := 'Closed'
        };


        WITH MODULE test
        INSERT User {
            name := 'Elvis'
        };

        WITH MODULE test
        INSERT User {
            name := 'Yury'
        };

        WITH MODULE test
        INSERT URL {
            name := 'edgedb.com',
            address := 'https://edgedb.com'
        };

        WITH MODULE test
        INSERT File {
            name := 'screenshot.png'
        };

        WITH MODULE test
        INSERT LogEntry {
            owner := (SELECT User FILTER User.name = 'Elvis'),
            spent_time := 50000,
            body := 'Rewriting everything.'
        };

        WITH MODULE test
        INSERT Issue {
            number := '1',
            name := 'Release EdgeDB',
            body := 'Initial public release of EdgeDB.',
            owner := (SELECT User FILTER User.name = 'Elvis'),
            watchers := (SELECT User FILTER User.name = 'Yury'),
            status := (SELECT Status FILTER Status.name = 'Open'),
            time_spent_log := (SELECT LogEntry),
            time_estimate := 3000
        };

        WITH MODULE test
        INSERT Comment {
            body := 'EdgeDB needs to happen soon.',
            owner := (SELECT User FILTER User.name = 'Elvis'),
            issue := (SELECT Issue FILTER Issue.number = '1')
        };


        WITH MODULE test
        INSERT Issue {
            number := '2',
            name := 'Improve EdgeDB repl output rendering.',
            body := 'We need to be able to render data in tabular format.',
            owner := (SELECT User FILTER User.name = 'Yury'),
            watchers := (SELECT User FILTER User.name = 'Elvis'),
            status := (SELECT Status FILTER Status.name = 'Open'),
            priority := (SELECT Priority FILTER Priority.name = 'High'),
            references :=
                (SELECT URL FILTER URL.address = 'https://edgedb.com')
                UNION
                (SELECT File FILTER File.name = 'screenshot.png')
        };

        WITH
            MODULE test,
            I := (SELECT Issue)
        INSERT Issue {
            number := '3',
            name := 'Repl tweak.',
            body := 'Minor lexer tweaks.',
            owner := (SELECT User FILTER User.name = 'Yury'),
            watchers := (SELECT User FILTER User.name = 'Elvis'),
            status := (SELECT Status FILTER Status.name = 'Closed'),
            related_to := (
                SELECT I FILTER I.number = '2'
            ),
            priority := (SELECT Priority FILTER Priority.name = 'Low')
        };

        WITH
            MODULE test,
            I := (SELECT Issue)
        INSERT Issue {
            number := '4',
            name := 'Regression.',
            body := 'Fix regression introduced by lexer tweak.',
            owner := (SELECT User FILTER User.name = 'Elvis'),
            status := (SELECT Status FILTER Status.name = 'Closed'),
            related_to := (
                SELECT I FILTER I.number = '3'
            )
        };

        # NOTE: UPDATE Users for testing the link properties
        #
        WITH MODULE test
        UPDATE User
        FILTER User.name = 'Elvis'
        SET {
            todo := (SELECT Issue FILTER Issue.number IN ['1', '2'])
        };

        WITH MODULE test
        UPDATE User
        FILTER User.name = 'Yury'
        SET {
            todo := (SELECT Issue FILTER Issue.number IN ['3', '4'])
        };

        #
        # MODULE testlp
        #

        # create some cards
        WITH MODULE testlp
        INSERT Card {
            name := 'Imp',
            element := 'Fire',
            cost := 1
        };

        WITH MODULE testlp
        INSERT Card {
            name := 'Dragon',
            element := 'Fire',
            cost := 5
        };

        WITH MODULE testlp
        INSERT Card {
            name := 'Bog monster',
            element := 'Water',
            cost := 2
        };

        WITH MODULE testlp
        INSERT Card {
            name := 'Giant turtle',
            element := 'Water',
            cost := 3
        };

        WITH MODULE testlp
        INSERT Card {
            name := 'Dwarf',
            element := 'Earth',
            cost := 1
        };

        WITH MODULE testlp
        INSERT Card {
            name := 'Golem',
            element := 'Earth',
            cost := 3
        };

        WITH MODULE testlp
        INSERT Card {
            name := 'Sprite',
            element := 'Air',
            cost := 1
        };

        WITH MODULE testlp
        INSERT Card {
            name := 'Giant eagle',
            element := 'Air',
            cost := 2
        };

        WITH MODULE testlp
        INSERT Card {
            name := 'Djinn',
            element := 'Air',
            cost := 4
        };

        # create players & decks
        WITH MODULE testlp
        INSERT User {
            name := 'Alice',
            deck := (
                SELECT Card {@count := len(Card.element) - 2}
                FILTER .element IN ['Fire', 'Water']
            )
        };

        WITH MODULE testlp
        INSERT User {
            name := 'Bob',
            deck := (
                SELECT Card {@count := 3} FILTER .element IN ['Earth', 'Water']
            )
        };

        WITH MODULE testlp
        INSERT User {
            name := 'Carol',
            deck := (
                SELECT Card {@count := 5 - Card.cost} FILTER .element != 'Fire'
            )
        };

        WITH MODULE testlp
        INSERT User {
            name := 'Dave',
            deck := (
                SELECT Card {@count := 4 IF Card.cost = 1 ELSE 1}
                FILTER .element = 'Air' OR .cost != 1
            )
        };

        # update friends list
        WITH
            MODULE testlp,
            U2 := User
        UPDATE User
        FILTER User.name = 'Alice'
        SET {
            friends := (
                SELECT U2 {
                    @nickname :=
                        'Swampy'        IF U2.name = 'Bob' ELSE
                        'Firefighter'   IF U2.name = 'Carol' ELSE
                        'Grumpy'
                } FILTER U2.name IN ['Bob', 'Carol', 'Dave']
            )
        };

        WITH
            MODULE testlp,
            U2 := User
        UPDATE User
        FILTER User.name = 'Dave'
        SET {
            friends := (
                SELECT U2 FILTER U2.name = 'Bob'
            )
        };
    """

    @tb.expected_optimizer_failure
    async def test_edgeql_group_simple01(self):
        await self.assert_query_result(r'''
            WITH MODULE test
            GROUP
                User
            BY
                User.name
            SELECT
                count(ALL User.<owner)
            ORDER BY
                User.name;
        ''', [
            [4, 2],
        ])

    @tb.expected_optimizer_failure
    async def test_edgeql_group_simple02(self):
        await self.assert_query_result(r'''
            WITH MODULE test
            GROUP
                Issue
            BY
                Issue.time_estimate
            SELECT
                # count using link 'id'
                count(ALL Issue.id)
            ORDER BY
                Issue.time_estimate EMPTY FIRST;
        ''', [
            [3, 1],
        ])

    @tb.expected_optimizer_failure
    async def test_edgeql_group_simple03(self):
        await self.assert_query_result(r'''
            WITH MODULE test
            GROUP
                Issue
            BY
                Issue.time_estimate
            SELECT
                # count Issue directly
                count(ALL Issue)
            ORDER BY
                Issue.time_estimate EMPTY FIRST;
        ''', [
            [3, 1],
        ])

    @tb.expected_optimizer_failure
    async def test_edgeql_group_simple04(self):
        await self.assert_query_result(r'''
            WITH MODULE test
            GROUP
                Issue
            BY
                Issue.time_estimate
            SELECT
                # count Issue statuses, which should be same as counting
                # Issues, since the status link is *1
                count(ALL Issue.status.id)
            ORDER BY
                Issue.time_estimate EMPTY FIRST;
        ''', [
            [3, 1],
        ])

    @tb.expected_optimizer_failure
    async def test_edgeql_group_simple05(self):
        await self.assert_query_result(r'''
            WITH MODULE test
            GROUP
                Issue
            BY
                Issue.time_estimate
            SELECT
                # unusual qualifier for 'count'
                count(DISTINCT Issue.status.id)
            ORDER BY
                Issue.time_estimate EMPTY FIRST;
        ''', [
            [2, 1],
        ])

    @tb.expected_optimizer_failure
    async def test_edgeql_group_alias01(self):
        await self.assert_query_result(r'''
            WITH MODULE test
            GROUP
                Issue
            BY
                Issue.time_estimate
            SELECT _ := (
                count := count(ALL Issue.status.id),
                te := Issue.time_estimate > 0
            ) ORDER BY
                _.te EMPTY FIRST;

            WITH MODULE test
            GROUP
                Issue
            BY
                Issue.time_estimate
            SELECT _ := (
                count := count(ALL Issue.status.id),
                te := Issue.time_estimate > 0
            ) ORDER BY
                _.te EMPTY LAST;
        ''', [
            [{'count': 3, 'te': None}, {'count': 1, 'te': True}],
            [{'count': 1, 'te': True}, {'count': 3, 'te': None}],
        ])

    @tb.expected_optimizer_failure
    async def test_edgeql_group_nested01(self):
        await self.assert_query_result(r"""
            WITH MODULE test
            SELECT
                R := (
                    name := User.name,
                    issues := array_agg(ALL (
                        GROUP
                            User.<owner[IS Issue]
                        BY
                            User.<owner[IS Issue].status.name
                        SELECT (
                            status := User.<owner[IS Issue].status.name,
                            count := count(ALL User.<owner[IS Issue]),
                        )
                        ORDER BY
                            User.<owner[IS Issue].status.name
                    ))
                )
            ORDER BY R.name;
            """, [[
            {
                'name': 'Elvis',
                'issues': [{
                    'status': 'Closed',
                    'count': 1,
                }, {
                    'status': 'Open',
                    'count': 1,
                }]
            },
            {
                'name': 'Yury',
                'issues': [{
                    'status': 'Closed',
                    'count': 1,
                }, {
                    'status': 'Open',
                    'count': 1,
                }]
            },
        ]])

    async def test_edgeql_group_agg01(self):
        await self.assert_query_result(r"""
            SELECT
                schema::Concept {
                    l := array_agg(
                        ALL
                        schema::Concept.links.name
                        FILTER
                            schema::Concept.links.name IN [
                                'std::id',
                                'schema::name'
                            ]
                        ORDER BY schema::Concept.links.name ASC
                    )
                }
            FILTER
                schema::Concept.name = 'schema::PrimaryClass';
        """, [
            [{
                'l': ['schema::name', 'std::id']
            }]
        ])

    async def test_edgeql_group_agg02(self):
        await self.assert_query_result(r"""
            WITH MODULE test
            SELECT array_agg(
                ALL
                [<str>Issue.number, Issue.status.name]
                ORDER BY Issue.number);
        """, [
            [[['1', 'Open'], ['2', 'Open'], ['3', 'Closed'], ['4', 'Closed']]]
        ])

    @tb.expected_optimizer_failure
    async def test_edgeql_group_agg03(self):
        await self.assert_query_result(r"""
            WITH MODULE test
            GROUP
                Issue
            BY
                Issue.status.name
            SELECT (
                sum := sum(ALL <int>Issue.number),
                status := Issue.status.name,
            ) ORDER BY Issue.status.name;
        """, [
            [{
                'status': 'Closed',
                'sum': 7,
            }, {
                'status': 'Open',
                'sum': 3,
            }],
        ])

    @tb.expected_optimizer_failure
    async def test_edgeql_group_agg04(self):
        await self.assert_query_result(r"""
            WITH MODULE test
            GROUP
                Issue
            BY
                Issue.status.name
            SELECT
                _ := (
                    sum := sum(ALL <int>Issue.number),
                    status := Issue.status.name,
                )
            FILTER
                _.sum > 5
            ORDER BY
                Issue.status.name;
        """, [
            [{
                'status': 'Closed',
                'sum': 7,
            }],
        ])

    async def test_edgeql_group_returning01(self):
        await self.assert_query_result(r'''
            WITH MODULE test
            GROUP
                Issue
            BY
                Issue.time_estimate
            SELECT
                # since we're returning the same element for all of
                # the groups the expected resulting SET should only
                # have one element
                42;
        ''', [
            [42],
        ])

    @tb.expected_optimizer_failure
    async def test_edgeql_group_by_tuple01(self):
        await self.assert_query_result(r"""
            WITH MODULE test
            GROUP
                Issue
            BY
                Issue.status.name,
                Issue.time_estimate
            SELECT _ := (
                sum := sum(ALL <int>Issue.number),
                status := Issue.status.name,
                time_estimate := Issue.time_estimate
            ) ORDER BY Issue.status.name
                THEN Issue.time_estimate;
        """, [
            [{
                'status': 'Closed', 'sum': 7, 'time_estimate': None
            }, {
                'status': 'Open', 'sum': 2, 'time_estimate': None
            }, {
                'status': 'Open', 'sum': 1, 'time_estimate': 3000
            }],
        ])

    @tb.expected_optimizer_failure
    async def test_edgeql_group_by_tuple02(self):
        await self.assert_query_result(r"""
            WITH MODULE test
            GROUP
                Issue
            BY
                Issue.status.name,
                Issue.time_estimate
            SELECT (
                sum := sum(ALL <int>Issue.number),
                status := Issue.status.name,
                time_estimate := Issue.time_estimate
            ) ORDER BY Issue.status.name
                # ordering condition derived from one of the GROUP BY
                # expressions
                THEN Issue.time_estimate > 0;
        """, [
            [{
                'status': 'Closed', 'sum': 7, 'time_estimate': None
            }, {
                'status': 'Open', 'sum': 2, 'time_estimate': None
            }, {
                'status': 'Open', 'sum': 1, 'time_estimate': 3000
            }],
        ])

    @tb.expected_optimizer_failure
    async def test_edgeql_group_by_tuple03(self):
        await self.assert_query_result(r"""
            WITH MODULE test
            GROUP
                Issue
            BY
                Issue.status.name,
                Issue.time_estimate
            SELECT (
                # array_agg with ordering instead of sum
                numbers := array_agg(
                    ALL <int>Issue.number ORDER BY Issue.number),
                status := Issue.status.name,
                time_estimate := Issue.time_estimate
            ) ORDER BY Issue.status.name
                THEN Issue.time_estimate;
        """, [
            [{
                'status': 'Closed',
                'time_estimate': None,
                'numbers': [3, 4],
            }, {
                'status': 'Open',
                'time_estimate': None,
                'numbers': [2],
            }, {
                'status': 'Open',
                'time_estimate': 3000,
                'numbers': [1],
            }],
        ])

    @tb.expected_optimizer_failure
    async def test_edgeql_group_by_tuple04(self):
        await self.assert_query_result(r"""
            WITH MODULE test
            GROUP
                Issue
            BY
                Issue.status.name,
                Issue.time_estimate
            SELECT (
                # array_agg with ordering instead of sum
                numbers := array_agg(ALL Issue.number ORDER BY Issue.number),
                status := Issue.status.name,
                time_estimate := Issue.time_estimate
            ) ORDER BY Issue.status.name
                THEN Issue.time_estimate;
        """, [
            [{
                'status': 'Closed',
                'time_estimate': None,
                'numbers': ['3', '4'],
            }, {
                'status': 'Open',
                'time_estimate': None,
                'numbers': ['2'],
            }, {
                'status': 'Open',
                'time_estimate': 3000,
                'numbers': ['1'],
            }],
        ])

    @tb.expected_optimizer_failure
    async def test_edgeql_group_by_tuple05(self):
        await self.assert_query_result(r"""
            WITH MODULE test
            GROUP
                Issue
            BY
                Issue.status.name,
                Issue.time_estimate
            SELECT (
                # a couple of array_agg
                numbers := array_agg(
                    ALL <int>Issue.number ORDER BY Issue.number),
                watchers := array_agg(
                    ALL <str>Issue.watchers.name ORDER BY Issue.watchers.name),
                status := Issue.status.name,
                time_estimate := Issue.time_estimate
            ) ORDER BY Issue.status.name
                THEN Issue.time_estimate;
        """, [
            [{
                'status': 'Closed',
                'time_estimate': None,
                'numbers': [3, 4],
                'watchers': ['Elvis'],
            }, {
                'status': 'Open',
                'time_estimate': None,
                'numbers': [2],
                'watchers': ['Elvis'],
            }, {
                'status': 'Open',
                'time_estimate': 3000,
                'numbers': [1],
                'watchers': ['Yury'],
            }],
        ])

    @tb.expected_optimizer_failure
    async def test_edgeql_group_by_tuple06(self):
        await self.assert_query_result(r"""
            WITH MODULE test
            GROUP
                Issue {
                    less_than_four := <int>Issue.number < 4
                }
            BY
                Issue.status.name,
                # group by computed link
                Issue.less_than_four
            SELECT (
                numbers := array_agg(
                    ALL Issue.number ORDER BY Issue.number),
                # watchers will sometimes be EMPTY resulting in []
                watchers := array_agg(
                    ALL Issue.watchers.name ORDER BY Issue.watchers.name),
                status := Issue.status.name,
            ) ORDER BY
                Issue.status.name
                THEN Issue.less_than_four;
        """, [
            [{
                'status': 'Closed',
                'numbers': ['4'],
                'watchers': []
            }, {
                'status': 'Closed',
                'numbers': ['3'],
                'watchers': ['Elvis']
            }, {
                'status': 'Open',
                'numbers': ['1', '2'],
                'watchers': ['Elvis', 'Yury']
            }],
        ])

    @tb.expected_optimizer_failure
    async def test_edgeql_group_by_tuple07(self):
        await self.assert_query_result(r"""
            WITH MODULE test
            GROUP
                Issue
            BY
                Issue.status.name,
                # group by non-atomic expression
                <int>Issue.number < 4
            SELECT _ := (
                numbers := array_agg(
                    ALL <int>Issue.number ORDER BY Issue.number),
                watchers := count(DISTINCT Issue.watchers),
                status := Issue.status.name,
            ) ORDER BY
                Issue.status.name
                THEN _.watchers
                # should work because count evaluates to a SINGLETON
                THEN count(DISTINCT Issue);
        """, [
            [{
                'status': 'Closed',
                'numbers': [4],
                'watchers': 0
            }, {
                'status': 'Closed',
                'numbers': [3],
                'watchers': 1
            }, {
                'status': 'Open',
                'numbers': [1, 2],
                'watchers': 2
            }],
        ])

    @unittest.expectedFailure
    async def test_edgeql_group_by_tuple08(self):
        await self.assert_query_result(r"""
            WITH MODULE test
            GROUP
                Issue
            BY
                Issue.status.name,
                Issue.owner.id
            SELECT (
                numbers := array_agg(
                    ALL <int>Issue.number ORDER BY Issue.number),
                status := Issue.status.name,
            ) ORDER BY Issue.status.name
                # should work because owner.name and owner.id are 1-1
                THEN Issue.owner.name;
        """, [
            [{
                'status': 'Closed',
                'numbers': [4],
            }, {
                'status': 'Closed',
                'numbers': [3],
            }, {
                'status': 'Open',
                'numbers': [1],
            }, {
                'status': 'Open',
                'numbers': [2],
            }],
        ])

    @tb.expected_optimizer_failure
    async def test_edgeql_group_linkproperty01(self):
        await self.assert_query_result(r"""
            WITH MODULE testlp
            GROUP
                Card
            BY
                Card.<deck@count
            SELECT _ := (
                cards := array_agg(
                    DISTINCT Card.name ORDER BY Card.name),
                count := Card.<deck@count,
            ) ORDER BY _.count;
        """, [
            [
                {
                    'cards': ['Bog monster', 'Djinn', 'Dragon', 'Giant eagle',
                              'Giant turtle', 'Golem'],
                    'count': 1
                },
                {
                    'cards': ['Dragon', 'Giant turtle', 'Golem', 'Imp'],
                    'count': 1
                },
                {
                    'cards': ['Bog monster', 'Dwarf', 'Giant eagle',
                              'Giant turtle', 'Golem'],
                    'count': 2
                },
                {
                    'cards': ['Dwarf', 'Sprite'],
                    'count': 4
                },
            ],
        ])