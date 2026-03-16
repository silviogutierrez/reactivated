import React from "react";

import {templates} from "@reactivated";

import {Layout} from "@client/components/Layout";
import * as forms from "@client/forms";

export const Template = (props: templates.PollsIndex) => (
    <Layout title="Polls" className="flex flex-col gap-2.5">
        <h1>Polls</h1>
        {props.latest_question_list.length > 0 ? (
            <ul>
                {props.latest_question_list.map((question) => (
                    <li key={question.id}>
                        <a href={`/polls/${question.id}`}>{question.question_text}</a>
                    </li>
                ))}
            </ul>
        ) : (
            <p>No polls are available.</p>
        )}
        <forms.ButtonLink href="/polls/create/">Create a new question</forms.ButtonLink>
    </Layout>
);
