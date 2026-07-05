<?php
/**
 * Plugin Name: WorkToolsLab Author Box
 * Description: Custom author box for singular posts. Name links to dedicated profile; archive link for all posts.
 * Version: 1.1.0
 *
 * Live path: wp-content/mu-plugins/worktoolslab-author-box.php
 * Repository mirror — manual deployment only. See docs/WORDPRESS_MU_PLUGIN_DEPLOYMENT_STATE_2026_07.md
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'WORKTOOLSLAB_AUTHOR_PROFILE_URL', 'https://worktoolslab.com/about/hayssam-dennaoui/' );

/**
 * Enqueue Kadence author-box styles plus inline WorkToolsLab overrides.
 */
function worktoolslab_author_box_enqueue_styles() {
	if ( ! is_singular( 'post' ) ) {
		return;
	}

	wp_enqueue_style(
		'kadence-author-box',
		get_template_directory_uri() . '/assets/css/author-box.min.css',
		array(),
		'1.4.5'
	);

	$inline_css = '.worktoolslab-author-box{margin-top:var(--global-md-spacing,2rem);padding-top:var(--global-md-spacing,2rem);border-top:1px solid var(--global-gray-400,#eee);}.worktoolslab-author-box__view-all{margin:0.75rem 0 0;font-size:0.9em;}.worktoolslab-author-box__view-all a{text-decoration:none;}';

	wp_add_inline_style( 'kadence-author-box', $inline_css );
}
add_action( 'wp_enqueue_scripts', 'worktoolslab_author_box_enqueue_styles', 20 );

/**
 * Render custom author box on singular posts only.
 */
function worktoolslab_render_author_box( $content ) {
	if ( ! is_singular( 'post' ) || ! in_the_loop() || ! is_main_query() ) {
		return $content;
	}

	$post_id = get_the_ID();
	if ( ! $post_id ) {
		return $content;
	}

	$author_id = (int) get_post_field( 'post_author', $post_id );
	if ( $author_id <= 0 ) {
		return $content;
	}

	$author      = get_userdata( $author_id );
	$author_name = $author ? $author->display_name : get_the_author();
	$author_bio  = $author ? get_the_author_meta( 'description', $author_id ) : '';
	$archive_url = get_author_posts_url( $author_id );
	$profile_url = WORKTOOLSLAB_AUTHOR_PROFILE_URL;

	ob_start();
	?>
	<div class="entry-author entry-author-style-normal worktoolslab-author-box">
		<div class="entry-author-profile author-profile vcard">
			<b class="entry-author-name author-name fn">
				<a href="<?php echo esc_url( $profile_url ); ?>" rel="author">
					<?php echo esc_html( $author_name ); ?>
				</a>
			</b>
			<?php if ( ! empty( $author_bio ) ) : ?>
				<div class="entry-author-description author-bio">
					<?php echo wpautop( wp_kses_post( $author_bio ) ); ?>
				</div>
			<?php endif; ?>
			<p class="worktoolslab-author-box__view-all">
				<a href="<?php echo esc_url( $archive_url ); ?>">
					<?php
					printf(
						/* translators: %s: author display name */
						esc_html__( 'View all posts by %s', 'worktoolslab' ),
						esc_html( $author_name )
					);
					?>
				</a>
			</p>
		</div>
	</div>
	<?php
	$box = ob_get_clean();

	return $content . $box;
}
add_filter( 'the_content', 'worktoolslab_render_author_box', 25 );
