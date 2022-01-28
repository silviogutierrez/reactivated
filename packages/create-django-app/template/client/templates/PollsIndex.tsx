import React from "react";

import {Types} from "@client/generated";
import {Layout} from "@client/components/Layout";

import {css} from "@linaria/core";

export default (props: Types["PollsIndexProps"]) => (
    <Layout title="Polls">
        {props.latest_question_list.length > 0 ? (
            <ul
                className={css`
                    padding: 15px;
                    max-width: 800px;
                    margin: 0 auto;
                `}
            >
                {props.latest_question_list.map((question) => (
                    <li key={question.id}>
                        <a href={`/polls/${question.id}`}>{question.question_text}</a>
                    </li>
                ))}
            </ul>
        ) : (
            <p>No polls are available.</p>
        )}
    </Layout>
);
