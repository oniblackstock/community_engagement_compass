from django.db import migrations


ABOUT_CONTENT = """
<p>Health Justice has built the Community Engagement Compass: a resource for community and for health organizations ready to do engagement differently, grounded in the conviction that community self-determination is the goal. And better outcomes follow.</p>

<p>The Compass currently draws from the <a href="https://www.healthjustice.co/NYCDOHMHCEFramework" target="_blank">New York City Department of Health and Mental Hygiene (DOHMH) Community Engagement Framework</a>, with plans to add additional vetted frameworks as the tool grows. The NYC DOHMH framework provides concrete engagement categories and practical implementation guidance that health professionals can apply immediately. The Compass's crowdsource feature lets practitioners and community members contribute resources, so the knowledge base reflects lived experience alongside institutional frameworks.</p>

<h3>The Genesis of Compass</h3>

<p>Health governance is a site of democratic participation that rarely gets named as such. When a health department decides which neighborhoods get outreach resources, which communities are consulted on program design, or who gets a seat at the table during a crisis — those are governance decisions. They determine who has power over decisions that affect people's lives and bodies.</p>

<p>Community engagement is the mechanism by which communities exercise democratic voice in those decisions. Done well, it redistributes power from institutions to the people those institutions are supposed to serve. Done poorly, it reproduces the same exclusions while calling it partnership.</p>

<p>The Compass sits at that gap. It brings together evidence-informed frameworks and community-contributed knowledge into searchable, citable, actionable guidance that anyone can access. Practitioners gain knowledge they were never trained in. Communities gain accountability from the institutions that make decisions about their lives. The most effective use of this tool involves organizations learning to follow community leadership while contributing their expertise and resources in ways that strengthen community self-reliance.</p>

<p>True partnership requires that health organizations examine their own practices, policies, and assumptions, and understand that communities determine their own engagement processes, health priorities, and solutions.</p>
""".strip()


def update_about_content(apps, schema_editor):
    AboutContent = apps.get_model('chat', 'AboutContent')
    # Update existing active content or create new
    obj = AboutContent.objects.filter(is_active=True).first()
    if obj:
        obj.content = ABOUT_CONTENT
        obj.save()
    else:
        AboutContent.objects.create(
            title="About Community Engagement Compass",
            content=ABOUT_CONTENT,
            is_active=True,
        )


def reverse_about_content(apps, schema_editor):
    pass  # No reverse needed


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0007_alter_aboutcontent_content_and_more'),
    ]

    operations = [
        migrations.RunPython(update_about_content, reverse_about_content),
    ]
